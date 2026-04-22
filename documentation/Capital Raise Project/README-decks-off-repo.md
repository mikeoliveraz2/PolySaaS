# Pitch decks no longer in Git

The `.pptx` files that used to live in this folder were tracked with **Git LFS**. GitHub **LFS budget limits** blocked **Render** (and other) clones when LFS could not download objects.

Those binaries were **removed from the repository** and **ignored** via `.gitignore` so future commits stay off LFS.

**Where to keep decks now:** team Drive / SharePoint, GitHub **Releases** attachments, or another store — link from internal docs or the investor site as needed.

To restore a copy locally, use backups outside this repo or Git history **before** the LFS-removal commit (if you still have LFS bandwidth or a machine that already smudged the files).
