# MMD-Project

## Project overview 

### Architecture

Streamlit (tabs per sheet, data_editor grids, forms, dashboards).

FastAPI backend (auth, RBAC, Excel-like sheet data, Python formula engine).

PostgreSQL for storage; Alembic for migrations.

JWT tokens passed from Streamlit to API.

Audit of all edits; import/export CSV/Excel.

Optional: Celery/RQ for heavy recalcs/imports.

### Data flow

User logs in (Streamlit → FastAPI /auth/login) → gets access_token.

Streamlit shows assigned Documents and Sheets.

User edits cells in data_editor → Streamlit diffs → PATCH to /sheets/{id}/rows/{row} with token.

Backend validates RBAC, saves values, recomputes formulas (row & sheet), returns updated row(s).

Summary tabs auto reflect computed values after save.

### RBAC

Roles: SUPER_ADMIN, EDITOR, VIEWER.

Assignments: document_assignments (doc/sheet/columns/rows via scope_json).

Only Super Admin can:

create/delete/disable users,

assign access,

create/modify formulas,

hard delete data.

Editors can add/edit rows per scope; Viewers read-only.

### Data model (high level)

users, roles, user_roles

documents, sheets, columns

rows, cells (value_json + computed_json)

formulas (Python, trigger = row/sheet/manual)

document_assignments (RBAC scope)

audits

### Formula engine (Python)

Row trigger: re-run when a row changes; update computed columns.

Sheet trigger: aggregates (totals, averages) after any row change.

Manual trigger: recalc endpoint for Super Admin.

Safe sandbox (allow math, statistics, approved helpers only).

### Streamlit UI plan for multi-sheet Excel

Top-level selectbox → Document

Tabs → one per Sheet (order from Excel)

Grid sheets: st.data_editor with column configs (types, ranges, dropdowns)

Form sheets: sections with st.number_input, st.text_input, st.selectbox

Dashboard sheets: KPIs, charts (computed by backend and returned)

Save changes button per sheet → calls PATCH per changed row

Role-aware widgets: disable editing for Viewers; show Admin settings panel only for Super Admin (user management, assignments, formula editor)
