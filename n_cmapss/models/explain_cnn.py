"""Read-only CNN diagnostic analysis. No retraining or test-set access."""
import argparse
from datetime import datetime
from pathlib import Path
import json
import h5py
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge


def names(h, key):
    return [x.decode() if isinstance(x, bytes) else str(x) for x in h[key][:].reshape(-1)]


def main():
    root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('experiment', type=Path, help='Folder containing fold_1 ... fold_6')
    p.add_argument('--h5', type=Path, default=root/'n_cmapss/data/N-CMAPSS_DS02-006.h5')
    p.add_argument('--metadata', type=Path, default=root/'n_cmapss/processed/window_metadata.csv')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    pred = []
    for path in sorted(args.experiment.glob('fold_*/validation_predictions.csv')):
        d = pd.read_csv(path)
        d['fold'] = int(path.parent.name.split('_')[-1])
        pred.append(d)
    if len(pred) != 6:
        raise ValueError('Exactly six fold prediction files are required.')
    d = pd.concat(pred, ignore_index=True)
    if d.window_id.duplicated().any():
        raise ValueError('Duplicate validation window IDs across folds')
    meta = pd.read_csv(args.metadata)
    d = d.merge(meta, on='window_id', suffixes=('', '_meta'), validate='one_to_one')
    if len(d) != sum(len(x) for x in pred) or len(d) != len(meta):
        raise ValueError('Predictions and metadata do not cover the same windows')
    for col in ['unit', 'cycle']:
        if not (d[col] == d[col+'_meta']).all():
            raise ValueError(f'{col} mismatch')
    if not np.allclose(d.true_rul, d.rul):
        raise ValueError('RUL mismatch')
    d = d.sort_values('window_id').reset_index(drop=True)
    out = args.out or args.experiment / ('diagnostics_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True, exist_ok=False)
    with h5py.File(args.h5, 'r') as h:
        groups = [('W_dev', names(h, 'W_var')), ('X_s_dev', names(h, 'X_s_var')),
                  ('T_dev', names(h, 'T_var'))]
        controls, sensors, health = [n for _, n in groups]
        acols = names(h, 'A_var')
        arrays = {k: [] for k, _ in groups}
        for i, row in enumerate(d.itertuples()):
            a, b = int(row.start_row), int(row.end_row)
            if not 0 <= a < b <= len(h['Y_dev']):
                raise ValueError('Invalid row interval')
            ids = h['A_dev'][a:b]
            if not (np.all(ids[:, acols.index('unit')] == row.unit) and
                    np.all(ids[:, acols.index('cycle')] == row.cycle)):
                raise ValueError('Window crosses a motor or flight boundary')
            if not np.allclose(h['Y_dev'][a:b], row.true_rul):
                raise ValueError('HDF5 target mismatch')
            for key, _ in groups:
                values = h[key][a:b]
                if not np.isfinite(values).all():
                    raise ValueError(f'Non-finite HDF5 values: {key}')
                arrays[key].append(values.mean(axis=0))
            if i % 500 == 0:
                print(f'Read {i}/{len(d)} windows', flush=True)
        for key, columns in groups:
            values = np.asarray(arrays[key])
            for j, col in enumerate(columns):
                d[col] = values[:, j]
    d['error'] = d.predicted_rul-d.true_rul
    d['abs_error'] = d.error.abs()
    # Each motor's sensor-condition model is fitted ONLY on the other motors.
    # All life stages are included: residuals are descriptive, not health estimates.
    residual_cols = []
    for sensor in sensors:
        col = sensor+'_condition_residual'
        residual_cols.append(col)
        d[col] = np.nan
    support = []
    for unit in sorted(d.unit.unique()):
        train, val = d[d.unit != unit], d[d.unit == unit]
        model = make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), Ridge(alpha=10))
        model.fit(train[controls], train[sensors])
        d.loc[val.index, residual_cols] = val[sensors].to_numpy()-model.predict(val[controls])
        outside = ((val[controls] < train[controls].min()) | (val[controls] > train[controls].max())).any(axis=1)
        support.append(dict(unit=int(unit), outside_training_marginal_range_fraction=float(outside.mean())))
    d.to_csv(out/'window_diagnostics.csv', index=False)
    flight = d.groupby(['fold','unit','cycle'], as_index=False)[
        ['true_rul','predicted_rul','error','abs_error']+controls+sensors+health+residual_cols].mean()
    flight['abs_mean_error'] = flight.error.abs()
    flight.to_csv(out/'flight_diagnostics.csv', index=False)
    d['rul_band'] = pd.cut(d.true_rul, [-np.inf,10,25,50,np.inf], labels=['0-10','11-25','26-50','51+'])
    rows=[]
    for (unit, band), g in d.groupby(['unit','rul_band'], observed=True):
        rows.append(dict(unit=unit, rul_band=str(band), n=len(g), mae=g.abs_error.mean(),
                         rmse=np.sqrt(np.mean(g.error**2)), bias=g.error.mean(),
                         overestimate_fraction=(g.error>0).mean()))
    bands=pd.DataFrame(rows); bands.to_csv(out/'rul_band_metrics.csv',index=False)
    correlations=[]
    for unit,g in flight.groupby('unit'):
        for col in controls+sensors+health+residual_cols:
            for target in ['error','abs_error']:
                value = g[col].corr(g[target], method='spearman') if g[col].nunique()>1 and g[target].nunique()>1 else np.nan
                correlations.append(dict(unit=unit, feature=col, target=target, spearman=value))
    pd.DataFrame(correlations).to_csv(out/'flight_correlations.csv',index=False)
    pd.DataFrame(support).to_csv(out/'condition_support.csv',index=False)
    with PdfPages(out/'diagnostic_figures.pdf') as pdf:
        def save(fig,name):
            fig.tight_layout(); fig.savefig(out/(name+'.png'),dpi=160); pdf.savefig(fig); plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(13,5))
        for ax,metric in zip(axes,['mae','bias']):
            table=bands.pivot(index='unit',columns='rul_band',values=metric).reindex(columns=['0-10','11-25','26-50','51+'])
            im=ax.imshow(table,cmap='viridis' if metric=='mae' else 'coolwarm',aspect='auto',
                         **({} if metric=='mae' else {'vmin':-abs(table.to_numpy()).max(),'vmax':abs(table.to_numpy()).max()}))
            ax.set_xticks(range(4),table.columns);ax.set_yticks(range(len(table)),table.index)
            ax.set(xlabel='True RUL band',ylabel='Motor',title=metric.upper()+' (window level)')
            for i in range(len(table)):
                for j in range(4):ax.text(j,i,f'{table.iloc[i,j]:.2f}',ha='center',va='center',color='white')
            fig.colorbar(im,ax=ax)
        save(fig,'01_error_by_life_stage')
        for unit,g in flight.groupby('unit'):
            g=g.sort_values('cycle');x=g.cycle
            fig,axes=plt.subplots(4,1,figsize=(12,12),sharex=True)
            axes[0].plot(x,g.true_rul,label='True RUL',color='black');axes[0].plot(x,g.predicted_rul,label='Mean prediction')
            axes[0].set_title(f'Motor {unit}: matched prediction windows, averaged per flight')
            axes[1].plot(x,g.error,label='Mean signed error');axes[1].plot(x,g.abs_error,label='Mean absolute window error')
            axes[1].axhline(0,color='black',ls='--')
            for col in controls:
                sd=g[col].std();axes[2].plot(x,(g[col]-g[col].mean())/sd if sd>0 else g[col]*0,label=col)
            for col in health:axes[3].plot(x,g[col],label=col)
            for ax,label in zip(axes,['RUL cycles','Error cycles','Conditions (within-motor z)','Health modifier']):
                ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=3)
            axes[-1].set_xlabel('Flight cycle');save(fig,f'motor_{unit}_overview')
            for group_name,columns in [('sensors',sensors),('condition_residuals',residual_cols)]:
                fig,axes=plt.subplots(4,4,figsize=(15,11),sharex=True)
                for ax,col in zip(axes.flat,columns):
                    ax.plot(x,g[col],lw=1);ax.set_title(col.replace('_condition_residual',''),fontsize=9);ax.grid(alpha=.2)
                for ax in list(axes.flat)[len(columns):]:ax.set_visible(False)
                fig.suptitle(f'Motor {unit}: {group_name}; flight means of selected windows',fontsize=14)
                fig.supxlabel('Flight cycle');save(fig,f'motor_{unit}_{group_name}')
    notes = {
        'purpose':'Descriptive diagnosis; no CNN weights, predictions, or baseline files modified.',
        'aggregation':'Exact model windows -> arithmetic window means -> equal-window flight means. Not full-flight means.',
        'T_parameters':'Diagnostic only, never CNN inputs.',
        'condition_residuals':'Sensor minus quadratic Ridge prediction from W; fit on other development motors, all life stages. Fixed alpha=10. Not a causal correction or a healthy baseline.',
        'limitations':['Time and RUL confound correlations; adjacent flights are dependent.',
                       'No p-values or causal claims. Low endpoint error does not establish fault detection performance.',
                       'Marginal range coverage does not guarantee joint operating-condition overlap.',
                       'Window means lose within-window dynamics used by CNN.',
                       'Validation motors were used for epoch selection; this is not independent test performance.']}
    (out/'interpretation_notes.json').write_text(json.dumps(notes,indent=2),encoding='utf-8')
    print('Saved diagnostics:',out)

if __name__=='__main__':
    main()
