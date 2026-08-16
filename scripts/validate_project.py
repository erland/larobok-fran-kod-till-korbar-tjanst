#!/usr/bin/env python3
from __future__ import annotations
import re, subprocess, sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MARKERS=('TODO','TBD','[SKRIV','[FYLL I','Lorem ipsum')

def main()->int:
    errors=[]
    integrity=subprocess.run([sys.executable,'scripts/project_integrity.py','verify','.'],cwd=ROOT,text=True,capture_output=True)
    if integrity.returncode!=0: errors.append('Projektets integritetsverifiering misslyckades: '+(integrity.stderr or integrity.stdout).strip())
    sys.path.insert(0,str(ROOT/'scripts'))
    import importlib.util
    spec=importlib.util.spec_from_file_location('export_book',ROOT/'scripts/export-book.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    try:
        text=mod.read_book_yaml(); meta=mod.metadata(text); chapters=mod.resolve_chapters(text); mod.validate_markdown(chapters)
    except SystemExit as exc: errors.append(str(exc)); chapters=[]; meta={}
    if meta and not meta.get('project_slug'): errors.append('book.yaml saknar project_slug')
    if meta and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',meta.get('project_slug','')): errors.append('project_slug måste vara en gemen kebab-case slug')
    for path in chapters:
        text=path.read_text(encoding='utf-8')
        if not text.strip(): errors.append(f'{path.relative_to(ROOT)} är tom')
        if sum(1 for line in text.splitlines() if re.match(r'^#\s+',line))!=1: errors.append(f'{path.relative_to(ROOT)} ska ha exakt en H1')
        mfile=re.match(r'^(\d{2})-', path.name)
        first=next((line.strip() for line in text.splitlines() if line.strip()), '')
        if mfile and mfile.group(1)!='00':
            mh1=re.fullmatch(r'#\s+(\d+)\.\s+.+', first)
            if not mh1 or int(mh1.group(1))!=int(mfile.group(1)): errors.append(f'{path.relative_to(ROOT)} ska börja med H1 som matchar kapitelnumret')
        for marker in MARKERS:
            if marker.lower() in text.lower(): errors.append(f'{path.relative_to(ROOT)} innehåller arbetsmarkören {marker}')
        for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)',text):
            ref=m.group(1).split()[0].strip('<>')
            if ref.startswith(('http://','https://')): continue
            target=(path.parent/ref).resolve()
            try: target.relative_to(ROOT.resolve())
            except ValueError: errors.append(f'{path.relative_to(ROOT)} har bildreferens utanför projektet: {ref}'); continue
            if not target.exists(): errors.append(f'{path.relative_to(ROOT)} saknar bildfil: {ref}')
    if errors:
        print('Validation failed:\n- '+'\n- '.join(errors),file=sys.stderr); return 1
    print(f"OK: projektvalidering godkänd. {len(chapters)} boktextfiler, profil={meta.get('book_kind')}."); return 0
if __name__=='__main__': raise SystemExit(main())
