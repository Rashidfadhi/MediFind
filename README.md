# MediFind

MediFind is a FastAPI application for finding medicines at pharmacies. Customers can search available stock and compare prices. Administrators manage the pharmacy and medicine catalogues, and pharmacy owners maintain their inventory.

## Requirements

- Python 3.10 or newer
- MySQL 8 or a compatible MySQL server

## Install and run (Windows PowerShell)

From this directory (`MediFind`):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a MySQL database and application user, then update `MEDIFIND_DATABASE_URL` in `.env`. URL-encode special characters in the database password. Replace `MEDIFIND_SECRET_KEY` with a unique secret generated with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Load the variables from `.env` into the current PowerShell session and start the server:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1])" -Value $matches[2] }
}
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs>.

## First administrator

Public registration always creates a customer account. To create the first administrator, register an account, then promote it directly in MySQL:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-admin@example.com';
```

Sign in at `/web/login`. The administrator dashboard lets you add pharmacies and medicines and assign pharmacy owners. Owners must first register as customers.

## Main pages and API

- `/` — medicine search landing page
- `/registration` and `/web/login` — customer registration and web sign-in
- `/web/admin/dashboard` — administrator management interface
- `/owner/dashboard` and `/owner/inventory` — pharmacy owner tools
- `/docs` — interactive API documentation
- `/pharmacies`, `/medicines`, `/inventory` — JSON endpoints

The application creates missing tables at startup with SQLAlchemy. For production, run behind HTTPS and set `MEDIFIND_COOKIE_SECURE=true`. Schema changes to existing databases should be applied through a database migration process; `create_all` does not alter existing tables.
