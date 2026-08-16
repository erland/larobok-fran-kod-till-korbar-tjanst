#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256();
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',required=True); args=ap.parse_args(); out=Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'scripts/validate_project.py','.'],cwd=ROOT,check=True)
    # export-book.py reads project_slug from book.yaml and writes directly to the requested directory.
    subprocess.run([sys.executable,'scripts/export-book.py','--format','all','--output-dir',str(out)],cwd=ROOT,check=True)
    files=sorted(list(out.glob('*.epub'))+list(out.glob('*.pdf')))
    if len([p for p in files if p.suffix=='.epub'])!=1 or len([p for p in files if p.suffix=='.pdf'])!=1: raise SystemExit('Bygget ska ge exakt en EPUB och en PDF')
    (out/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(p)}  {p.name}' for p in files)+'\n',encoding='utf-8')
    print('Bygge klart:',', '.join(p.name for p in files)); return 0
if __name__=='__main__': raise SystemExit(main())
