# Weightlifting Tracker

A Streamlit frontend with Supabase (Postgres) backend for building and logging weightlifting workouts. Includes Strava integration to post "Weight Training" activities.

## What's included

- Database migration: `migrations/0001_weightlifting_schema.sql`
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
supabase_key = "your-service-role-or-api-key"

[strava]
access_token = "YOUR_STRAVA_ACCESS_TOKEN"
```

Notes:
- `supabase_key` may be the anon public key for client-side or a service_role key for server-side operations depending on your use case. Keep secrets secure.
- If you do not provide `strava.access_token`, Strava upload attempts will be skipped and a warning will be shown.

Authentication (Magic Link)

- In the Supabase console go to `Authentication` → `Emails` (or `Authentication` → `Email` depending on console version) and enable **Magic Link** / passwordless sign-in.
- Add your app redirect URL(s) to the Allowed Redirect URLs list. For local development add `http://localhost:8501` and for Streamlit Cloud add your app URL (for example `https://share.streamlit.io/<your-user>/<your-repo>/main`).
- Use the anon/public `supabase_key` in your Streamlit secrets for client-side auth flows. The app provides a magic link sender and will capture the returned token on redirect.

After enabling Magic Link, the sidebar in the app lets you request a magic link to the email you provide. Clicking the emailed link will redirect back to the app and sign you in automatically.

4. Run the database migration

You can apply the SQL migration with the Supabase SQL editor, or via `psql` if you have direct DB access. Example using `psql`:

```bash
psql "postgresql://<db_user>:<db_password>@<host>:5432/<db_name>" -f migrations/0001_weightlifting_schema.sql
```

Or paste the contents of `migrations/0001_weightlifting_schema.sql` into the Supabase SQL editor and run it.

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
- Timed exercises render an inline timer with 5s count-in and 5s count-out and an automatic beep.
- Strava integration creates `WeightTraining` activities — ensure `strava.access_token` has `write` scopes.

If you'd like, I can also:

- Add a `README` section for Supabase CLI usage and CI deployment.
- Add a Dockerfile or Procfile for hosting.
