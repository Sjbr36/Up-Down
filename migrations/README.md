# Migrations

This folder contains SQL migration files for the Weightlifting Tracker application.

Migrations:

- `0001_weightlifting_schema.sql` - creates schema for `exercises`, `workout_templates`, `template_exercises`, `workout_logs`, and `set_logs`, plus seed data.
- `0002_user_auth_rls.sql` - adds Supabase Auth user ownership and Row Level Security policies for user-specific workout data.

How to apply:

- Supabase SQL editor: open the SQL editor in your Supabase project and paste the SQL file contents, then run each migration in filename order.
- psql: if you have direct database access run:

```bash
psql "postgresql://<user>:<password>@<host>:<port>/<database>" -f migrations/0001_weightlifting_schema.sql
psql "postgresql://<user>:<password>@<host>:<port>/<database>" -f migrations/0002_user_auth_rls.sql
```

- Supabase CLI: you may run ad-hoc SQL from the CLI or integrate the SQL file into your preferred migrations workflow.

Rollback:

These migrations are additive. To remove them, drop the RLS policies and ownership columns, then drop the tables via the Supabase SQL editor or create reverse migrations that undo the changes in the correct order.
