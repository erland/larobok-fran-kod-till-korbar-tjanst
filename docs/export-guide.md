# Exportguide

`book.yaml` är enda kanoniska metadata- och kapitelordningskällan.

## Lokalt
```bash
python3 scripts/validate_project.py .
python3 scripts/export-book.py --format all
```
Pandoc 3.1.11.1 rekommenderas. PDF kräver XeLaTeX och TeX Gyre Pagella.

## GitHub
- Validate körs på pull request och push till `main`.
- Build Preview startas manuellt och ger ett gemensamt artifact med EPUB, PDF och SHA256SUMS.
- Release triggas av `v<SemVer>` och publicerar EPUB/PDF som separata release-assets.

Arbetsfiler i `docs/` exporteras aldrig som boktext.
