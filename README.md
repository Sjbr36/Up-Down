# Weightlifting Tracker

A Streamlit frontend with Supabase (Postgres) backend for building and logging weightlifting workouts. Includes Strava integration to post "Weight Training" activities.

## What's included

- Database migrations: `migrations/0001_weightlifting_schema.sql`, `migrations/0002_user_auth_rls.sql`, `migrations/0003_supersets.sql`
- Streamlit app: `app.py`
- Supabase integration helper: `database.py`
- Strava integration helper: `strava.py`
- Requirements: `requirements.txt`

## Prerequisites

- Python 3.10+ (3.12 tested)
- A Supabase project (Postgres) with API key
- Optional: Strava API access token for activity uploads

## Setup (local)

1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd
.\.venv\Scripts\activate.bat
```

2. Install Python dependencies

```bash
pip install -r requirements.txt
```

3. Configure Streamlit secrets

Create a file at `.streamlit/secrets.toml` with the following keys (or use Streamlit Cloud secrets):

```toml
# .streamlit/secrets.toml
supabase_url = "https://your-project-ref.supabase.co"
supabase_key = "your-supabase-anon-public-key"

[strava]
access_token = "YOUR_STRAVA_ACCESS_TOKEN"
```

Notes:
- Users sign in through Supabase Auth with email and password.
- Use the Supabase anon public key for `supabase_key`. Do not use a service role key in the Streamlit app because service role keys bypass Row Level Security.
- If you do not provide `strava.access_token`, Strava upload attempts will be skipped and a warning will be shown.
- For password reset links, add an optional `password_reset_redirect_to` secret pointing at your app URL, such as `http://localhost:8501` for local testing or `https://your-streamlit-app.streamlit.app` for production. The app will read the recovery token from that URL and show a password-entry form automatically.

Create the first three users in Supabase Dashboard > Authentication > Users. The app does not expose public sign-up; only users you create in Supabase can sign in.

4. Run the database migration

Apply the SQL migrations in order with the Supabase SQL editor, or via `psql` if you have direct DB access. Example using `psql`:

```bash
psql "postgresql://<db_user>:<db_password>@<host>:5432/<db_name>" -f migrations/0001_weightlifting_schema.sql
psql "postgresql://<db_user>:<db_password>@<host>:5432/<db_name>" -f migrations/0002_user_auth_rls.sql
psql "postgresql://<db_user>:<db_password>@<host>:5432/<db_name>" -f migrations/0003_supersets.sql
```

Or paste the contents of each migration into the Supabase SQL editor and run them in filename order.

`0002_user_auth_rls.sql` adds `user_id` ownership columns and enables Row Level Security so each authenticated user can only access their own workout templates, workout logs, and set history. Existing templates and workout logs without a `user_id` will be hidden by RLS until you assign them to a Supabase Auth user.

`0003_supersets.sql` adds optional superset metadata for template exercises.

5. Run the app

```bash
streamlit run app.py
```

Open the displayed local URL on your phone or desktop.

## Deployment

- Deploy the database migration to your Supabase project (SQL editor or CI using Supabase CLI).
- Host the Streamlit app on a VM, Streamlit Cloud, or other hosting provider. Ensure `.streamlit/secrets.toml` or environment secrets are configured.
- The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml`.

## GitHub Actions and auto deployment

- Every push to `main` will run CI, validate the app, and build/publish a Docker image to GitHub Container Registry at `ghcr.io/<your-org-or-user>/weightlifting-tracker:latest`.
- To deploy automatically on push with Streamlit Cloud, connect this repository in Streamlit Cloud and enable auto-deploy for the `main` branch.
- If you want a container-based deployment, use the generated `Dockerfile` to run the app anywhere Docker is supported.

## Docker deployment

This project includes a `Dockerfile` to package the app as a container image.

Build locally:

```bash
docker build -t weightlifting-tracker:latest .
```

Run locally:

```bash
docker run -p 8501:8501 \
  -e STREAMLIT_SERVER_HEADLESS=true \
  weightlifting-tracker:latest
```

## Notes and tips

- The app uses button-only interactions for quick gym use (weight +/-5, reps +/-1).
- Template exercises can be paired into two-exercise supersets labeled A, B, or C; the logger alternates each pair by set number.
- Timed exercises render an inline timer with 5s count-in and 5s count-out and an automatic beep.
- Strava integration creates `WeightTraining` activities — ensure `strava.access_token` has `write` scopes.

If you'd like, I can also:

- Add a `README` section for Supabase CLI usage and CI deployment.
- Add a Dockerfile or Procfile for hosting.
