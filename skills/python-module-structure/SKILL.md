---
name: python-module-structure
description: Use when creating, splitting or reviewing Python files and packages in a backend repo — file length, where constants, exceptions, SQL and shared helpers live, `__init__.py` files, or a file that mixes unrelated concerns.
---

# Python Module Structure

File-level rules from MR review. Function-level style: `production-python-style`. DTO/adapter files: `dtos-and-adapters`. Responsibilities: `solid-principles`.

## Rules

1. **No file over 400 lines.** Split along a responsibility seam (not alphabetically). Why: long files hide mixed concerns.
2. **Constants at the top of the module.** If another module needs one, move it to its own file (`constants.py`, or a topic file) and import it; do not leave it mid-file. Topic constants that grow get a topic file (e.g. `billing_columns.py` rather than one giant `constants.py`). Masks, flags and helpers are not constants: put them with the code that uses them.
3. **One `exceptions.py` per package.** Every custom exception in the package lives there, never inline in `service.py`, `writer.py`, `exporter.py`.
4. **No unneeded `__init__.py`.** Namespace packages work; add one only when it holds real exports or the tooling demands it. Do not add them to test directories.
5. **Delete files that exist for one tiny thing** (a `schemas.py` with one class): put it beside its user until a second consumer appears.
6. **Name a file for what it holds.** A function that does not match the file's name (`resolver.py` containing a query builder) moves.
7. **Shared code lives in the shared package**, not copy-pasted across services. When two services need the same logic, flag it and extract it to the shared library.
8. **SQL has a home**: a repository, `sql.py`, or a domain provider class (`OrdersSQLProvider`, `report_aggs.py`). Never inline in a service, route or helper.
9. **Generic cross-cutting helpers** (gzip responses, pagination) go in a generic module (`api/gzip.py`), not inside one feature's routes.
10. **One service, repository or route resource per file.** Several services → `services/<name>.py`; several repositories → `repositories/<aggregate>.py`; routes for several resources → `routes/<resource>.py` plus a small `router.py` that sets the prefix and includes them. No `__init__.py` needed (rule 4). Why: a reviewer finds a class by its file name, and one per file keeps diffs scoped.
11. **Name a file after its domain content, not the transport or mechanism**: `invoice_columns.py` (the columns each export carries), not `exports.py`. Extends rule 6.

## Audit a diff

- [ ] `wc -l` on changed files: none over 400.
- [ ] Constants: top of module or own file; none mid-file.
- [ ] `class \w+(Error|Exception)` outside `exceptions.py`: none.
- [ ] New `__init__.py`: each justified.
- [ ] SQL strings / `text(` outside repository/`sql.py`/provider: none.
- [ ] Each file's functions match its name.
- [ ] At most one `class \w*(Service|Repository)` per file; each route module serves one resource.
