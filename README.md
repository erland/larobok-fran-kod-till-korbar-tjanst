# Från kod till körbar tjänst

Bokprojekt för faktaboken *Från kod till körbar tjänst – PWA med React och TypeScript, Quarkus, PostgreSQL och Docker* av Erland Lindmark.

Projektet är skapat från Lärobokskaparens kanoniska projektmall.

## Profil
- `book_kind`: `factbook`
- `book_type`: `subject_overview`
- nivå: erfaren utvecklare
- genomgående case: TaskBoard

## Arbetsflöde
1. Plan och canon finns under `docs/`.
2. Boktext ligger under `chapters/` och följer ordningen i `book.yaml`.
3. Referensimplementationen ska ligga under `code/taskboard/`.
4. Kodexempel i boken ska hållas konsekventa med referensimplementationen.
5. Källor och tidskänsliga tekniska fakta verifieras mot primärkällor och registreras i `docs/faktakontroll.md`.
6. Verifiera projektintegritet före och efter filändringar med `scripts/project_integrity.py`.
7. Bygg EPUB/PDF reproducerbart med `scripts/export-book.py` när manus finns.

## GitHub Actions och publicering
- `01-validate.yml` validerar PR/push till `main`.
- `02-build-preview.yml` bygger EPUB/PDF manuellt.
- `03-release.yml` bygger på `v*`-tagg och publicerar EPUB/PDF som release-assets.
