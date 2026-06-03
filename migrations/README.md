# Migrations

This folder contains SQL migration files for the Weightlifting Tracker application.

Primary migration:

- `0001_weightlifting_schema.sql` — creates schema for `exercises`, `workout_templates`, `template_exercises`, `workout_logs`, and `set_logs`, plus seed data.

How to apply:

- Supabase SQL editor: open the SQL editor in your Supabase project and paste the SQL file contents, then run.
- psql: if you have direct database access run:

```bash
psql "postgresql://<user>:<password>@<host>:<port>/<database>" -f migrations/0001_weightlifting_schema.sql
```

- Supabase CLI: you may run ad-hoc SQL from the CLI or integrate the SQL file into your preferred migrations workflow.

Rollback:

This initial migration is additive. To remove it, drop the tables via the Supabase SQL editor or create a reverse-migration that drops the created tables in the correct order (child tables first).
