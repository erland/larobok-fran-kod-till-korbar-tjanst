#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, hashlib, json, re, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

MANIFEST='project-manifest.json'; LOG='revision-log.md'; IGNORED={'.git','.DS_Store','__MACOSX','__pycache__'}
CHAPTER_RE=re.compile(r'^chapters/(\d{2})-[a-z0-9][a-z0-9-]*\.md$',re.I)

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def digest(p):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def inventory(root):
    out={}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        r=p.relative_to(root)
        if r.as_posix()==MANIFEST or any(x in IGNORED for x in r.parts) or p.suffix=='.pyc': continue
        out[r.as_posix()]={'sha256':digest(p),'bytes':p.stat().st_size}
    return out
def summary(files):
    items={}
    by_number={}
    for path,info in files.items():
        m=CHAPTER_RE.fullmatch(path)
        if not m or m.group(1)=='00':
            continue
        number=int(m.group(1))
        if number in by_number:
            raise ValueError(f'Dubbla kapitelfiler för kapitel {number:02d}: {by_number[number]}, {path}')
        by_number[number]=path
        items[path]=info['sha256']
    nums=sorted(by_number)
    return {'count':len(nums),'latest':nums[-1] if nums else None,'hashes':items}
def load(root): return json.loads((root/MANIFEST).read_text(encoding='utf-8'))
def save(root,m): (root/MANIFEST).write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def compare(a,b):
    A=set(a); B=set(b)
    return sorted(B-A),sorted(A-B),sorted(p for p in A&B if a[p]!=b[p])
def append_log(root,rev,op,changed,zname):
    p=root/LOG
    if not p.exists(): p.write_text('# Revisionslogg\n\n| Revision | Tidpunkt (UTC) | Åtgärd | Ändrade filer | Zip-fil |\n|---:|---|---|---|---|\n',encoding='utf-8')
    files=', '.join(f'`{x}`' for x in changed) or 'Inga'
    with p.open('a',encoding='utf-8') as f: f.write(f'| {rev} | {now()} | {op.replace("|","/")} | {files} | `{zname}` |\n')
def root(v):
    p=Path(v).resolve()
    if not p.is_dir(): raise ValueError(f'Projektkatalog saknas: {p}')
    return p

def verify(r):
    m=load(r)
    if m.get('template'): raise ValueError('Manifestet är fortfarande en mall. Kör init för ett konkret projekt.')
    if not m.get('project_id') or not isinstance(m.get('revision'),int) or m['revision']<1: raise ValueError('Manifestet saknar giltigt project_id/revision')
    actual=inventory(r); add,rem,chg=compare(m.get('tracked_files',{}),actual)
    if add or rem or chg: raise ValueError(f'Integritetsfel: tillagda={add}, borttagna={rem}, ändrade={chg}')
    if summary(actual)!=m.get('chapters'): raise ValueError('Kapitelöversikten matchar inte filerna')
    return m

def cmd_init(a):
    r=root(a.root); mp=r/MANIFEST
    if mp.exists():
        old=json.loads(mp.read_text(encoding='utf-8'))
        if not old.get('template'): raise ValueError('init får inte köras på redan initierat projekt')
    files=inventory(r); rev=a.revision
    m={'schema_version':1,'template':False,'project_id':str(uuid.uuid4()),'project_slug':a.slug,'revision':rev,'parent_revision':None,'created_at':now(),'updated_at':now(),'canonical_zip_name':a.zip_name,'tracked_files':files,'chapters':summary(files),'last_operation':{'operation':a.operation,'source_revision':None,'changed_files':sorted(files)}}
    save(r,m); append_log(r,rev,a.operation,sorted(files),a.zip_name); m['tracked_files']=inventory(r); m['chapters']=summary(m['tracked_files']); save(r,m)
    print(f'OK: init revision {rev}, project_id={m["project_id"]}'); return 0

def cmd_verify(a):
    m=verify(root(a.root)); print(f'OK: revision {m["revision"]}, project_id={m["project_id"]}, kapitel={m["chapters"]["count"]}'); return 0

def cmd_status(a):
    r=root(a.root); m=load(r); actual=inventory(r); add,rem,chg=compare(m.get('tracked_files',{}),actual)
    print(json.dumps({'revision':m.get('revision'),'added':add,'removed':rem,'changed':chg},ensure_ascii=False,indent=2)); return 1 if rem else 0

def cmd_commit(a):
    r=root(a.root); m=load(r)
    if m.get('template'): raise ValueError('Kör init först')
    if m.get('revision')!=a.expected_revision: raise ValueError(f'Förväntade revision {a.expected_revision}, fick {m.get("revision")}')
    actual=inventory(r); add,rem,chg=compare(m['tracked_files'],actual); changed=sorted(add+rem+chg)
    disallowed=[p for p in changed if not any(fnmatch.fnmatch(p,x) for x in a.allow)]
    if disallowed: raise ValueError('Ej tillåtna ändringar: '+', '.join(disallowed))
    old_hashes=m.get('chapters',{}).get('hashes',{})
    for p,h in old_hashes.items():
        if p not in changed and actual.get(p,{}).get('sha256')!=h: raise ValueError(f'Oavsiktlig kapiteländring: {p}')
    newrev=m['revision']+1; append_log(r,newrev,a.operation,changed,a.zip_name); actual=inventory(r)
    m.update({'parent_revision':a.expected_revision,'revision':newrev,'updated_at':now(),'canonical_zip_name':a.zip_name,'tracked_files':actual,'chapters':summary(actual),'last_operation':{'operation':a.operation,'source_revision':a.expected_revision,'changed_files':changed}}); save(r,m)
    print(f'OK: revision {newrev}; ändrade={changed}'); return 0

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    x=s.add_parser('init'); x.add_argument('root'); x.add_argument('--slug',required=True); x.add_argument('--revision',type=int,default=1); x.add_argument('--zip-name',required=True); x.add_argument('--operation',default='Initierade bokprojekt'); x.set_defaults(fn=cmd_init)
    x=s.add_parser('verify'); x.add_argument('root'); x.set_defaults(fn=cmd_verify)
    x=s.add_parser('status'); x.add_argument('root'); x.set_defaults(fn=cmd_status)
    x=s.add_parser('commit'); x.add_argument('root'); x.add_argument('--expected-revision',type=int,required=True); x.add_argument('--operation',required=True); x.add_argument('--zip-name',required=True); x.add_argument('--allow',action='append',default=[]); x.set_defaults(fn=cmd_commit)
    a=p.parse_args()
    try: return a.fn(a)
    except (ValueError,FileNotFoundError,json.JSONDecodeError) as e: print('FEL:',e,file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
