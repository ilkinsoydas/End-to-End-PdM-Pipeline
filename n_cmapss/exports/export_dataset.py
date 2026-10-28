"""Model-independent filtered N-CMAPSS CSV exporter. Run --help for usage."""
import argparse
import csv
import hashlib
import json
import operator
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np

GROUPS = ('A', 'W', 'X_s', 'X_v', 'T')
OPS = {'ge': operator.ge, 'gt': operator.gt, 'le': operator.le,
       'lt': operator.lt, 'eq': operator.eq, 'ne': operator.ne}


def catalog(h, partition):
    result = {}
    total = h[f'A_{partition}'].shape[0]
    for group in GROUPS:
        key = f'{group}_{partition}'
        if key not in h:
            continue
        labels = [v.decode('utf-8') if isinstance(v, bytes) else str(v)
                  for v in h[f'{group}_var'][:].reshape(-1)]
        if h[key].ndim != 2 or h[key].shape != (total, len(labels)):
            raise ValueError(f'Inconsistent dataset shape: {key}')
        for col, name in enumerate(labels):
            if name in result:
                raise ValueError(f'Duplicate column name in HDF5: {name}')
            result[name] = (key, col, group)
    if 'RUL' in result or h[f'Y_{partition}'].shape != (total, 1):
        raise ValueError('Invalid RUL dataset')
    result['RUL'] = (f'Y_{partition}', 0, 'Y')
    for required in ('unit', 'cycle'):
        if required not in result:
            raise ValueError(f'Missing {required}')
    return result


def read_columns(h, cat, columns, start, end):
    # Read each requested group once, preserving caller's column order.
    blocks = {cat[c][0]: None for c in columns}
    for key in blocks:
        blocks[key] = h[key][start:end]
    return np.column_stack([blocks[cat[c][0]][:, cat[c][1]] for c in columns])


def flight_segments(h, cat, partition, chunk_size):
    """Scan only unit/cycle in chunks; yields half-open, contiguous segments."""
    previous = None
    start = 0
    total = h[f'A_{partition}'].shape[0]
    seen = set()
    for offset in range(0, total, chunk_size):
        values = read_columns(h, cat, ['unit', 'cycle'], offset, min(total, offset+chunk_size))
        if not np.isfinite(values).all() or not np.equal(values, np.floor(values)).all():
            raise ValueError('unit/cycle must be finite integers')
        changes = np.r_[0, np.flatnonzero(np.any(values[1:] != values[:-1], axis=1))+1]
        for i in changes:
            pair = tuple(map(int, values[i]))
            if pair != previous:
                if previous is not None:
                    yield (*previous, start, offset+int(i))
                if pair in seen:
                    raise ValueError(f'Noncontiguous repeated flight: {pair}')
                seen.add(pair)
                previous, start = pair, offset+int(i)
    if previous is not None:
        yield (*previous, start, total)


def row_mask(values, positions, rules):
    mask = np.ones(len(values), dtype=bool)
    for col, conditions in rules.items():
        v = values[:, positions[col]]
        mask &= np.isfinite(v)
        for op, expected in conditions.items():
            if op == 'in':
                mask &= np.isin(v, expected)
            else:
                mask &= OPS[op](v, expected)
    return mask


def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def validate(c, cat):
    allowed = {'name','data_path','output_root','partition','columns','units','cycles',
               'filters','window','exports','chunk_rows','sequence_features'}
    if set(c)-allowed:
        raise ValueError(f'Unknown configuration keys: {sorted(set(c)-allowed)}')
    if not c.get('columns') or len(set(c['columns'])) != len(c['columns']):
        raise ValueError('columns must be a nonempty unique list')
    for name in c['columns']:
        if name not in cat:
            raise ValueError(f'Unknown column {name}. Use --list-columns.')
    for col, rules in c.get('filters', {}).items():
        if col not in cat or not isinstance(rules, dict) or not rules:
            raise ValueError(f'Invalid filter: {col}')
        if set(rules)-set(OPS)-{'in'}:
            raise ValueError(f'Unsupported filter operation for {col}')
        for op, value in rules.items():
            values = value if op == 'in' else [value]
            if op == 'in' and (not isinstance(value, list) or not value):
                raise ValueError('in filter requires a nonempty list')
            if not all(isinstance(v,(int,float)) and np.isfinite(v) for v in values):
                raise ValueError('Filters require finite numeric values')
    for key in ['units','cycles']:
        if key in c and (not isinstance(c[key],list) or not c[key] or
                         any(type(v) is not int for v in c[key])):
            raise ValueError(f'{key}: omit for all, or provide a nonempty integer list')
    chunk = c.get('chunk_rows', 100000)
    if type(chunk) is not int or chunk < 1:
        raise ValueError('chunk_rows must be a positive integer')
    w = c.get('window')
    exports = c.get('exports', {'raw':True,'window_values':True,'statistics':True,'sequences':False})
    if set(exports)-{'raw','window_values','statistics','sequences'} or any(type(v) is not bool for v in exports.values()):
        raise ValueError('Invalid exports settings')
    if w is not None:
        if set(w)-{'size','stride','target'}:
            raise ValueError('Unknown window setting')
        for key in ('size','stride'):
            if type(w.get(key)) is not int or w[key] < 1:
                raise ValueError(f'window.{key} must be a positive integer')
        if w.get('target','last') not in ('last','mean'):
            raise ValueError('window.target must be last or mean')
    elif any(exports.get(k,False) for k in ('window_values','statistics','sequences')):
        raise ValueError('Window exports require a window configuration')
    features = c.get('sequence_features',[s for s in c['columns'] if cat[s][2] in ('W','X_s')])
    if exports.get('sequences',False):
        if not features or len(set(features))!=len(features):
            raise ValueError('Unique nonempty sequence_features required')
        if any(s not in c['columns'] or cat[s][2] not in ('W','X_s') for s in features):
            raise ValueError('Sequence features must be selected W/X_s columns; diagnostic groups remain CSV only')
    return exports, features


def export(config, base=None):
    if isinstance(config, dict):
        c = json.loads(json.dumps(config))
    else:
        c = json.loads(
            Path(config).read_text(encoding="utf-8")
        )
    base=Path(base or Path.cwd()).resolve()
    path=Path(c['data_path']);path=path if path.is_absolute() else base/path
    partition=c.get('partition','dev')
    if partition not in ('dev','test'):
        raise ValueError('partition must be dev or test')
    with h5py.File(path,'r') as h:
        cat=catalog(h,partition);exports,features=validate(c,cat)
        # Include provenance separately; selected data column order stays unchanged.
        columns=c['columns'];rules=c.get('filters',{})
        needed=list(dict.fromkeys(columns+list(rules)+['RUL']))
        pos={col:i for i,col in enumerate(needed)}
        w=c.get('window');chunk=c.get('chunk_rows',100000)
        stat=path.stat()
        identity={'config':c,'source_path':str(path.resolve()),'source_size':stat.st_size,
                  'source_mtime_ns':stat.st_mtime_ns}
        digest=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:12]
        root=Path(c.get('output_root','n_cmapss/exports'));root=root if root.is_absolute() else base/root
        name=c.get('name','exports')
        if not isinstance(name,str) or not name or any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for x in name):
            raise ValueError('name must contain only letters, digits, underscore or hyphen')
        out=root/f'{name}_{digest}_{datetime.now():%Y%m%d_%H%M%S_%f}'
        out.mkdir(parents=True,exist_ok=False)
        manifest={**identity,'export_id':digest,'partition':partition,'status':'building',
                  'source_identity_note':'Path/size/mtime fingerprint, NOT a content hash.',
                  'selected_columns':columns,'sequence_features':features,'scaled':False,
                  'rules':{'window_origin':'flight_start','end_row':'exclusive','tail':'drop',
                           'filters':'raw rows individually; candidate window accepted only if ALL rows pass',
                           'std_ddof':0,'source_row':'zero-based row in selected HDF5 partition'}}
        dump_json(out/'manifest.json',manifest)
        try:
            return build(h,cat,c,exports,features,needed,pos,out,manifest,partition,chunk,w)
        except Exception as exc:
            manifest.update(status='failed',error=str(exc));dump_json(out/'manifest.json',manifest)
            raise


def build(h,cat,c,exports,features,needed,pos,out,manifest,partition,chunk,w):
    columns=c['columns'];rules=c.get('filters',{})
    counts=dict(selected_flights=0,source_rows_in_selected_flights=0,filtered_raw_rows=0,
                candidate_windows=0,accepted_windows=0,window_row_occurrences=0,unique_window_rows=0,
                raw_rows_written=0)
    window_records=[];unit_counts={};seen_units=set();seen_cycles=set()
    with ExitStack() as stack:
        def writer(name,header):
            f=stack.enter_context((out/name).open('w',newline='',encoding='utf-8-sig'))
            wr=csv.writer(f);wr.writerow(header);return wr
        raw=writer('raw.csv',['source_row','meta_unit','meta_cycle']+columns) if exports.get('raw',False) else None
        long=writer('window_values.csv',['window_id','step','source_row','meta_unit','meta_cycle']+columns) if exports.get('window_values',False) else None
        stats=writer('window_statistics.csv',['window_id','meta_unit','meta_cycle','target_rul']+
                     [f'{s}__{op}' for s in columns for op in ('mean','std','min','max')]) if exports.get('statistics',False) else None
        windows=writer('windows.csv',['window_id','unit','cycle','start_row','end_row','length','target_rul']) if w else None
        flights=writer('flights.csv',['unit','cycle','start_row','end_row','source_rows','filtered_rows',
                                      'candidate_windows','accepted_windows','unique_window_rows','uncovered_filtered_rows'])
        dictionary=writer('column_catalog.csv',['column','hdf5_dataset','index','group','selected','role'])
        for col,(key,j,group) in cat.items():
            role='target' if group=='Y' else ('model_input_candidate' if group in ('W','X_s') else 'metadata_or_diagnostic')
            dictionary.writerow([col,key,j,group,col in columns,role])
        units=set(c.get('units',[]));cycles=set(c.get('cycles',[]))
        for unit,cycle,a,b in flight_segments(h,cat,partition,chunk):
            seen_units.add(unit);seen_cycles.add(cycle)
            if (units and unit not in units) or (cycles and cycle not in cycles):continue
            counts['selected_flights']+=1;counts['source_rows_in_selected_flights']+=b-a
            passing=np.empty(b-a,dtype=bool);filtered=0
            for start in range(a,b,chunk):
                end=min(b,start+chunk);v=read_columns(h,cat,needed,start,end)
                mask=row_mask(v,pos,rules);passing[start-a:end-a]=mask
                n=int(mask.sum());filtered+=n
                if raw is not None:
                    selected=v[:,[pos[s] for s in columns]]
                    for idx in np.flatnonzero(mask):raw.writerow([start+int(idx),unit,cycle,*selected[idx]])
                    counts['raw_rows_written']+=n
            counts['filtered_raw_rows']+=filtered
            candidates=accepted=unique=0;covered_end=a
            if w:
                bad_prefix=np.r_[0,np.cumsum(~passing)]
                size,stride=w['size'],w['stride']
                for start in range(a,b-size+1,stride):
                    candidates+=1;end=start+size
                    if bad_prefix[end-a]!=bad_prefix[start-a]:continue
                    values=read_columns(h,cat,needed,start,end)
                    selected=values[:,[pos[s] for s in columns]]
                    if not np.isfinite(selected).all() or not np.isfinite(values[:,pos['RUL']]).all():
                        raise ValueError(f'Nonfinite window data at source row {start}')
                    target=float(values[-1,pos['RUL']] if w.get('target','last')=='last' else values[:,pos['RUL']].mean())
                    wid=counts['accepted_windows'];counts['accepted_windows']+=1;accepted+=1
                    unique+=end-max(start,covered_end);covered_end=max(covered_end,end)
                    windows.writerow([wid,unit,cycle,start,end,size,target])
                    if exports.get('sequences',False):window_records.append((start,end,target,unit,cycle))
                    if long is not None:
                        long.writerows([wid,i,start+i,unit,cycle,*row] for i,row in enumerate(selected))
                    if stats is not None:
                        summaries=np.column_stack([selected.mean(0),selected.std(0,ddof=0),selected.min(0),selected.max(0)])
                        stats.writerow([wid,unit,cycle,target,*summaries.ravel()])
            counts['candidate_windows']+=candidates;counts['unique_window_rows']+=unique
            counts['window_row_occurrences']+=accepted*(w['size'] if w else 0)
            unit_counts[unit]=unit_counts.get(unit,0)+accepted
            flights.writerow([unit,cycle,a,b,b-a,filtered,candidates,accepted,unique,filtered-unique])
            print(f'Unit {unit}, cycle {cycle}: {filtered} filtered rows, {accepted} windows',flush=True)
        if units-seen_units:raise ValueError(f'Unknown units: {sorted(units-seen_units)}')
        if cycles-seen_cycles:raise ValueError(f'Unknown cycles: {sorted(cycles-seen_cycles)}')
    if exports.get('sequences',False):
        n=len(window_records)
        if not n:raise ValueError('No windows available for sequence exports')
        x=np.lib.format.open_memmap(out/'X.npy',mode='w+',dtype=np.float32,shape=(n,w['size'],len(features)))
        y=np.lib.format.open_memmap(out/'y.npy',mode='w+',dtype=np.float32,shape=(n,))
        for i,(a,b,target,_,_) in enumerate(window_records):
            x[i]=read_columns(h,cat,features,a,b);y[i]=target
        x.flush();y.flush();del x,y
    counts['uncovered_filtered_rows']=counts['filtered_raw_rows']-counts['unique_window_rows']
    manifest.update(status='complete',counts=counts,windows_by_unit=unit_counts,
                    sequences_shape=([len(window_records),w['size'],len(features)] if exports.get('sequences',False) else None))
    dump_json(out/'manifest.json',manifest)
    dump_json(out/'config.json',c)
    print(f'Complete: {out}\n{json.dumps(counts,indent=2)}')
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path)
    p.add_argument('--list-columns',action='store_true')
    p.add_argument('--data',type=Path,default=Path('n_cmapss/data/N-CMAPSS_DS02-006.h5'))
    p.add_argument('--partition',choices=['dev','test'],default='dev')
    args=p.parse_args()
    if args.list_columns:
        with h5py.File(args.data,'r') as h:
            for name,(key,index,group) in catalog(h,args.partition).items():print(f'{name:20} {key:12} column={index} group={group}')
    elif args.config:export(args.config)
    else:p.error('Use --config FILE or --list-columns')


if __name__=='__main__':main()
