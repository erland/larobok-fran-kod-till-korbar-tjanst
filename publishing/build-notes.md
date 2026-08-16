# Build notes

Markdown under `chapters/` är kanonisk boktext. `book.yaml` styr metadata, kapitelordning och exportval.

## Reproducerbar build
- Pandoc är låst till 3.1.11.1 i GitHub Actions.
- PDF byggs med XeLaTeX och TeX Gyre Pagella.
- EPUB efterbearbetas av `fix-epub-after-pandoc.py`.
- Preview och Release använder `scripts/build_book.py`; workflow-YAML innehåller ingen boklogik.
- Arbetsfiler under `docs/` exporteras inte.
