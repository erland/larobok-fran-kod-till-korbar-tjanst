#!/usr/bin/env python3
from __future__ import annotations
import re, sys, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
OPF="http://www.idpf.org/2007/opf"; XHTML="http://www.w3.org/1999/xhtml"; EPUB="http://www.idpf.org/2007/ops"
NS={"opf":OPF,"x":XHTML,"epub":EPUB}

def rootfile(base: Path) -> Path:
    tree=ET.parse(base/'META-INF/container.xml')
    node=tree.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
    if node is None: raise RuntimeError('EPUB container saknar rootfile')
    return Path(node.attrib['full-path'])

def split_headings(base: Path)->int:
    count=0; pat=re.compile(r'^\s*(\d+)\.\s+(.+?)\s*$')
    for path in base.rglob('*.xhtml'):
        tree=ET.parse(path); changed=False
        for h1 in tree.getroot().findall('.//x:h1',NS):
            text=''.join(h1.itertext()).strip(); m=pat.match(text)
            if not m: continue
            ident=h1.attrib.get('id'); h1.clear()
            if ident: h1.set('id',ident)
            a=ET.SubElement(h1,f'{{{XHTML}}}span',{'class':'chapter-number'}); a.text=m.group(1)
            b=ET.SubElement(h1,f'{{{XHTML}}}span',{'class':'chapter-title'}); b.text=m.group(2)
            changed=True
        if changed: tree.write(path,encoding='utf-8',xml_declaration=True); count+=1
    return count

def nav_non_linear(base: Path, opf_rel: Path)->bool:
    path=base/opf_rel; tree=ET.parse(path); manifest=tree.getroot().find('opf:manifest',NS); spine=tree.getroot().find('opf:spine',NS)
    if manifest is None or spine is None: raise RuntimeError('EPUB OPF saknar manifest/spine')
    nav_ids={i.attrib['id'] for i in manifest.findall('opf:item',NS) if 'nav' in i.attrib.get('properties','').split()}
    changed=False
    for item in spine.findall('opf:itemref',NS):
        if item.attrib.get('idref') in nav_ids and item.attrib.get('linear')!='no': item.set('linear','no'); changed=True
    if changed: tree.write(path,encoding='utf-8',xml_declaration=True)
    return changed

def repack(base:Path,out:Path)->None:
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out,'w') as z:
        mime=base/'mimetype'; z.write(mime,'mimetype',compress_type=zipfile.ZIP_STORED)
        for p in sorted(base.rglob('*')):
            if p.is_file() and p!=mime: z.write(p,p.relative_to(base).as_posix(),compress_type=zipfile.ZIP_DEFLATED)

def validate(path:Path)->None:
    with zipfile.ZipFile(path) as z:
        if not z.namelist() or z.namelist()[0]!='mimetype' or z.getinfo('mimetype').compress_type!=zipfile.ZIP_STORED:
            raise RuntimeError('EPUB-fel: mimetype måste ligga först och vara okomprimerad')
        if 'META-INF/container.xml' not in z.namelist(): raise RuntimeError('EPUB-fel: container.xml saknas')

def main()->int:
    if len(sys.argv)!=2: print('Användning: fix-epub-after-pandoc.py <fil.epub>',file=sys.stderr); return 2
    epub=Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='fix-epub-') as td:
        base=Path(td)
        with zipfile.ZipFile(epub) as z: z.extractall(base)
        opf=rootfile(base); headings=split_headings(base); nav=nav_non_linear(base,opf); repack(base,epub)
    validate(epub); print(f'Efterbearbetad EPUB: kapitelfiler={headings}, nav linear=no={nav}'); return 0
if __name__=='__main__': raise SystemExit(main())
