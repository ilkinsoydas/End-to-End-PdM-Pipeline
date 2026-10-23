"""Evaluate frozen baseline CNNs under within-window temporal perturbations."""
import argparse
import json
import pickle
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from n_cmapss.features.dl_sequences import FeatureStandardizer, load_normalized_sequences
from n_cmapss.preprocessing.data_loader import load_window_metadata, split_windows_by_fold, load_feature_names


class CNNRegressor(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.feature_extractor = nn.Sequential(nn.Conv1d(channels,32,5,padding=2),nn.ReLU(),
            nn.Conv1d(32,64,5,padding=2),nn.ReLU(),nn.AdaptiveAvgPool1d(1))
        self.regressor = nn.Sequential(nn.Flatten(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,1))
    def forward(self,x):
        return self.regressor(self.feature_extractor(x)).squeeze(-1)


def perturb(x, mode, rng, block_size=16):
    # Shape: batch, time, channel. One permutation per window, shared by all channels.
    if mode == 'original':
        return x
    if mode == 'reverse':
        return x[:, ::-1, :].copy()
    n,t,c=x.shape
    indices=[]
    for _ in range(n):
        if mode == 'shuffle':
            order=rng.permutation(t)
        elif mode == 'block_shuffle':
            if t % block_size:
                raise ValueError('Window length must be divisible by block size')
            order=np.concatenate([np.arange(j*block_size,(j+1)*block_size)
                                  for j in rng.permutation(t//block_size)])
        else:
            raise ValueError(mode)
        indices.append(order)
    return np.take_along_axis(x,np.asarray(indices)[:,:,None],axis=1)


def scores(y,p):
    e=p-y
    return dict(mae=float(np.abs(e).mean()),rmse=float(np.sqrt(np.mean(e**2))),bias=float(e.mean()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment',type=Path,help='Original six-fold experiment folder')
    parser.add_argument('--folds',nargs='+',type=int,choices=range(1,7),default=list(range(1,7)))
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--seed',type=int,default=2026)
    parser.add_argument('--batch-size',type=int,default=64)
    args=parser.parse_args()
    if args.repeats<1 or args.batch_size<1 or len(set(args.folds))!=len(args.folds):
        parser.error('Positive repeats/batch-size and unique folds required')
    torch.set_num_threads(4)
    out=args.experiment/('temporal_probe_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True,exist_ok=False)
    metadata=load_window_metadata(); rows=[];bands=[]
    config=dict(folds=args.folds,repeats=args.repeats,seed=args.seed,batch_size=args.batch_size,
                block_size=16,device='cpu',retraining=False,
                interpretation='Frozen model sensitivity, not proof that temporal information is necessary. Synthetic input shift possible.')
    (out/'config.json').write_text(json.dumps(config,indent=2))
    (out/'analysis_source.py').write_text(Path(__file__).read_text())
    for fold in args.folds:
        folder=args.experiment/f'fold_{fold}'
        checkpoint=torch.load(folder/'best_model.pt',map_location='cpu',weights_only=True)
        if checkpoint['fold']!=fold or checkpoint['feature_names']!=load_feature_names():
            raise ValueError('Checkpoint fold/feature order mismatch')
        # Load only your own previously generated scaler files.
        with (folder/'scaler.pkl').open('rb') as f:
            scaler=FeatureStandardizer(pickle.load(f))
        _,records=split_windows_by_fold(metadata,fold_number=fold)
        x,y=load_normalized_sequences(records,scaler)
        if x.shape[1]!=checkpoint['window_size']:
            raise ValueError('Checkpoint window size mismatch')
        model=CNNRegressor(x.shape[2]);model.load_state_dict(checkpoint['model_state_dict'],strict=True);model.eval()
        saved=pd.read_csv(folder/'validation_predictions.csv').set_index('window_id')
        ids=[r.window_id for r in records]
        if not saved.index.is_unique or set(saved.index)!=set(ids):
            raise ValueError('Saved window IDs mismatch')
        saved=saved.loc[ids]
        if not np.allclose(saved.true_rul,y):raise ValueError('Target mismatch')
        details=pd.DataFrame(dict(window_id=ids,unit=[r.unit for r in records],
                                  cycle=[r.cycle for r in records],true_rul=y))
        original=None
        for mode in ['original','reverse','block_shuffle','shuffle']:
            for repeat in range(args.repeats if 'shuffle' in mode else 1):
                rng=np.random.default_rng(np.random.SeedSequence([args.seed,fold,repeat,
                                                ['original','reverse','block_shuffle','shuffle'].index(mode)]))
                predictions=[]
                with torch.no_grad():
                    for start in range(0,len(x),args.batch_size):
                        batch=perturb(x[start:start+args.batch_size],mode,rng)
                        tensor=torch.from_numpy(np.ascontiguousarray(batch.transpose(0,2,1)))
                        predictions.append(model(tensor).numpy())
                p=np.concatenate(predictions)
                if not np.isfinite(p).all():raise ValueError('Non-finite predictions')
                if mode=='original':
                    original=p.copy()
                    max_diff=float(np.max(abs(p-saved.predicted_rul.to_numpy())))
                    if max_diff>0.001:raise ValueError(f'Original predictions not reproduced: max difference {max_diff}')
                    print(f'Fold {fold}: original reproduced; max difference {max_diff:.8f}',flush=True)
                result=dict(fold=fold,unit=int(records[0].unit),mode=mode,repeat=repeat,n=len(y),
                            mean_prediction_shift=float(np.abs(p-original).mean()),**scores(y,p))
                rows.append(result)
                details[f'{mode}_{repeat}']=p
                for lo,hi in [(0,10),(11,25),(26,50),(51,np.inf)]:
                    mask=(y>=lo)&(y<=hi)
                    if mask.any():bands.append(dict(fold=fold,mode=mode,repeat=repeat,
                        rul_band=f'{lo}-{hi}',n=int(mask.sum()),**scores(y[mask],p[mask])))
                print(f"  {mode} repeat {repeat}: RMSE {result['rmse']:.3f}",flush=True)
        details.to_csv(out/f'fold_{fold}_predictions.csv',index=False)
        pd.DataFrame(rows).to_csv(out/'all_metrics.csv',index=False)
        pd.DataFrame(bands).to_csv(out/'rul_band_metrics.csv',index=False)
    df=pd.DataFrame(rows)
    summary=df.groupby(['fold','unit','mode'],as_index=False).agg(
        mae_mean=('mae','mean'),rmse_mean=('rmse','mean'),rmse_repeat_std=('rmse','std'),
        mean_prediction_shift=('mean_prediction_shift','mean'))
    baseline=summary[summary['mode']=='original'].set_index('fold').rmse_mean
    summary['rmse_delta']=summary.rmse_mean-summary.fold.map(baseline)
    summary.to_csv(out/'comparison.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    modes=['original','reverse','block_shuffle','shuffle'];folds=sorted(df.fold.unique());pos=np.arange(len(folds))
    for j,mode in enumerate(modes):
        g=summary[summary['mode']==mode].set_index('fold').loc[folds]
        axes[0].bar(pos+(j-1.5)*.2,g.rmse_mean,.2,label=mode,yerr=g.rmse_repeat_std.fillna(0),capsize=2)
        if mode!='original':axes[1].plot(folds,g.rmse_delta,marker='o',label=mode)
    axes[0].set_xticks(pos,folds);axes[0].set(xlabel='Fold',ylabel='Validation RMSE',title='Frozen CNN: temporal perturbations')
    axes[1].axhline(0,color='black',ls='--');axes[1].set(xlabel='Fold',ylabel='RMSE minus original',title='Change from original input')
    for ax in axes:ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(out/'temporal_comparison.png',dpi=180);plt.close(fig)
    print('Saved:',out)


if __name__=='__main__':
    main()
