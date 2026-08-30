# Industrial Engineering CGPA Portal

A Streamlit portal where Industrial Engineering students look up their name by registration number and submit their CGPA up to the 3rd semester, while admins review and delete submissions.

## Run & Operate

- `streamlit run app.py --server.port 5000` — run the portal locally
- `streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true` — run it for the Replit preview/deployment
- `cgpa_submissions.csv` — locally stored submission data
- Admin login: username `admin`, password `admin123`

## Stack

- Python 3.13
- Streamlit
- Pandas

## Where things live

- `app.py` — Streamlit UI, CSV persistence, student lookup, admin login, sorting, download, and deletion
- `students.csv` — supplied department roster
- `cgpa_submissions.csv` — submission storage file, created with headers

## Architecture decisions

- The roster is a read-only CSV so registration numbers and names can be updated without changing application logic.
- Each CGPA submission gets its own ID and timestamp, while a new submission replaces the student's previous record so admins see only the latest CGPA.
- Admin access is kept in a separate tab and only the admin session displays submission data.
- The app uses local CSV storage to keep the deployment simple and dependency-light.

## Product

- Students can search by registration number without creating an account.
- A matched student sees a welcome message and can submit a CGPA from 0.00 to 10.00.
- Admins can sign in, filter records, review all entries sorted by registration number, download CSV, and delete selected submissions.

## User preferences

- Keep the interface simple and easy to deploy with Streamlit.

## Gotchas

- The admin password is intentionally the requested default `admin123`; change it in `app.py` before sharing the deployed app publicly.
- Local CSV storage is appropriate for a lightweight deployment; a database or shared storage service is needed for multi-instance production persistence.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
