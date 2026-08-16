#!/usr/bin/env python3
from __future__ import annotations
import argparse, re, shutil, subprocess, tempfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
NUMBERED_CHAPTER_RE=re.compile(r'^\d{2}-[a-z0-9][a-z0-9-]*\.md$',re.I)
PANDOC_VERSION='3.1.11.1'

def scalar(text,key):
    m=re.search(rf'(?m)^{re.escape(key)}:\s*(?:"([^"]*)"|\'([^\']*)\'|([^#\n]*))',text)
    return next((g for g in m.groups() if g is not None),'').strip() if m else ''
def read_book_yaml():
    p=ROOT/'book.yaml'
    if not p.is_file(): raise SystemExit('Saknar book.yaml')
    return p.read_text(encoding='utf-8')
def metadata(text):
    keys=('title','subtitle','author','language','identifier','date','version','book_kind','book_type','cover_image','project_slug','subject','description')
    v={k:scalar(text,k) for k in keys}; missing=[k for k in ('title','author','language','book_kind','book_type','project_slug') if not v[k]]
    if missing: raise SystemExit('Saknad metadata i book.yaml: '+', '.join(missing))
    if v['book_kind'] not in ('textbook','factbook'): raise SystemExit('Ogiltig book_kind: '+v['book_kind'])
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v['project_slug']): raise SystemExit('project_slug måste vara gemen kebab-case')
    return v
def chapter_entries(text):
    lines=text.splitlines(); start=None; base=0
    for i,line in enumerate(lines):
        m=re.match(r'^(\s*)chapters:\s*(?:#.*)?$',line)
        if m: start=i+1; base=len(m.group(1)); break
    if start is None: raise SystemExit('book.yaml saknar chapters:-lista')
    out=[]
    for line in lines[start:]:
        if not line.strip() or line.lstrip().startswith('#'): continue
        indent=len(line)-len(line.lstrip())
        if indent<=base and not line.lstrip().startswith('-'): break
        m=re.match(r'^\s*-\s*(?:"([^"]+)"|\'([^\']+)\'|([^#\n]+?))\s*(?:#.*)?$',line)
        if not m: raise SystemExit('Ogiltig chapters-post: '+line.strip())
        out.append(next(g for g in m.groups() if g is not None).strip())
    if not out: raise SystemExit('chapters: är tom')
    return out
def resolve_chapters(text):
    entries=chapter_entries(text)
    if len(entries)!=len(set(entries)): raise SystemExit('Dubbellistade kapitel i book.yaml')
    if entries[0]!='chapters/00-inledning.md': raise SystemExit('Första chapters-posten ska vara chapters/00-inledning.md')
    paths=[]
    for e in entries:
        pure=PurePosixPath(e)
        if pure.is_absolute() or '..' in pure.parts or len(pure.parts)!=2 or pure.parts[0]!='chapters': raise SystemExit('Ogiltig kapitelsökväg: '+e)
        p=ROOT/pure.as_posix()
        if not p.is_file(): raise SystemExit('Listad kapitelfil saknas: '+e)
        if p.name.startswith('kapitelmall-'): raise SystemExit('Kapitelmall får inte exporteras: '+e)
        paths.append(p)
    listed={p.relative_to(ROOT).as_posix() for p in paths}; unlisted=[]
    for p in sorted((ROOT/'chapters').glob('*.md')):
        if NUMBERED_CHAPTER_RE.fullmatch(p.name) and p.relative_to(ROOT).as_posix() not in listed: unlisted.append(p.relative_to(ROOT).as_posix())
    if unlisted: raise SystemExit('Numrerade kapitelfiler saknas i book.yaml: '+', '.join(unlisted))
    return paths
def validate_markdown(paths):
    errors=[]
    for p in paths:
        t=p.read_text(encoding='utf-8')
        if re.search(r'(?m)^#{4,}\s',t): errors.append(p.name+': H4 eller djupare rubrik')
        if t.count('```')%2: errors.append(p.name+': obalanserade kodblock')
    if errors: raise SystemExit('Markdown-validering misslyckades:\n- '+'\n- '.join(errors))
def run(cmd): print('+',' '.join(map(str,cmd))); subprocess.run(cmd,cwd=ROOT,check=True)
def find_font_dir():
    for base in (Path('/usr/share/fonts'),Path('/usr/local/share/fonts')):
        if base.exists():
            for p in base.rglob('texgyrepagella-regular.otf'):
                names=['texgyrepagella-regular.otf','texgyrepagella-bold.otf','texgyrepagella-italic.otf','texgyrepagella-bolditalic.otf']
                if all((p.parent/n).is_file() for n in names): return p.parent
    return None
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--format',choices=['epub','pdf','all'],default='all'); ap.add_argument('--output-dir',default=str(ROOT/'exports')); args=ap.parse_args()
    if not shutil.which('pandoc'): raise SystemExit('Pandoc saknas')
    text=read_book_yaml(); meta=metadata(text); chapters=resolve_chapters(text); validate_markdown(chapters)
    out=Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True); slug=meta['project_slug']
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); body='\n\n'.join(p.read_text(encoding='utf-8').strip() for p in chapters)+'\n'; merged=td/'book.md'; merged.write_text(body,encoding='utf-8')
        common=['pandoc',str(merged),'--from=markdown+pipe_tables+fenced_code_blocks+fenced_divs','--standalone','--metadata-file',str(ROOT/'book.yaml')]
        if args.format in ('epub','all'):
            epub=out/f'{slug}.epub'
            cmd=['pandoc',str(merged),'--from=markdown+pipe_tables+fenced_code_blocks+fenced_divs','--to=epub3','--standalone','--toc','--toc-depth=1','--metadata-file',str(ROOT/'book.yaml'),'--css',str(ROOT/'publishing/epub.css')]
            cover=meta['cover_image'];
            if cover:
                cp=ROOT/cover
                if not cp.is_file(): raise SystemExit('Angiven omslagsbild saknas: '+cover)
                cmd += ['--epub-cover-image',str(cp)]
            run(cmd+['--output',str(epub)]); run([sys.executable,str(ROOT/'publishing/fix-epub-after-pandoc.py'),str(epub)])
        if args.format in ('pdf','all'):
            if not shutil.which('xelatex'): raise SystemExit('XeLaTeX saknas för PDF-export')
            pdf=out/f'{slug}.pdf'; cmd=common+['--top-level-division=chapter','--pdf-engine=xelatex','--template',str(ROOT/'publishing/pdf-template.tex'),'--lua-filter',str(ROOT/'publishing/pdf-filter.lua')]
            fontdir=find_font_dir()
            if fontdir: cmd += ['--metadata',f'pdf-font-dir={fontdir.as_posix()}/']
            cover=meta['cover_image']
            if cover:
                cp=ROOT/cover
                if not cp.is_file(): raise SystemExit('Angiven omslagsbild saknas: '+cover)
                cmd += ['--metadata',f'cover-image={cp.as_posix()}']
            run(cmd+['--output',str(pdf)])
    return 0
if __name__=='__main__':
    import sys
    raise SystemExit(main())
