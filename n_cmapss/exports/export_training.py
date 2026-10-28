"""Optional NumPy adapter. Importing this module never starts training."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def load_training_arrays(directory, validation_units, standardize=True, layout='NTC'):
    """Return (X_train, y_train, X_val, y_val, scaler, feature_names).

    StandardScaler is fitted on TRAIN windows only. T/hs/RUL cannot be features
    in exporter-created X.npy. Selection copies arrays into RAM; for very large
    exports use mmap X.npy and window metadata directly with a batched loader.
    NTC = [window,time,feature]; NCT = [window,feature,time].
    """
    from sklearn.preprocessing import StandardScaler
    path=Path(directory)
    manifest=json.loads((path/'manifest.json').read_text())
    if manifest['status']!='complete' or manifest['partition']!='dev':
        raise ValueError('Training adapter requires a complete dev exports')
    if layout not in ('NTC','NCT'):raise ValueError('layout must be NTC or NCT')
    x=np.load(path/'X.npy',mmap_mode='r',allow_pickle=False)
    y=np.load(path/'y.npy',mmap_mode='r',allow_pickle=False)
    meta=pd.read_csv(path/'windows.csv')
    if len(x)!=len(meta) or len(y)!=len(meta) or not np.allclose(y,meta.target_rul):
        raise ValueError('Sequence/metadata mismatch')
    requested=set(validation_units);available=set(meta.unit.unique())
    if not requested or requested-available:raise ValueError('Unknown or empty validation units')
    mask=meta.unit.isin(requested).to_numpy()
    if mask.all() or not mask.any():raise ValueError('Train and validation must both be nonempty')
    train=np.array(x[~mask],dtype=np.float32);val=np.array(x[mask],dtype=np.float32)
    scaler=None
    if standardize:
        scaler=StandardScaler()
        for i in range(0,len(train),64):scaler.partial_fit(train[i:i+64].reshape(-1,x.shape[2]))
        for values in (train,val):
            for i in range(0,len(values),64):
                block=values[i:i+64]
                values[i:i+64]=scaler.transform(block.reshape(-1,x.shape[2])).reshape(block.shape)
    if layout=='NCT':train,val=train.transpose(0,2,1),val.transpose(0,2,1)
    return train,np.array(y[~mask]),val,np.array(y[mask]),scaler,manifest['sequence_features']
