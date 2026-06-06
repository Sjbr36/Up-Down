-- Add per-user ownership and Row Level Security for Supabase Auth users.

alter table public.workout_templates
    add column if not exists user_id uuid references auth.users(id) on delete cascade;

alter table public.workout_logs
    add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- The original schema used ON DELETE SET NULL while template_id was NOT NULL.
alter table public.workout_logs
    alter column template_id drop not null;

create index if not exists idx_workout_templates_user_id on public.workout_templates(user_id);
create index if not exists idx_workout_logs_user_id on public.workout_logs(user_id);

alter table public.exercises enable row level security;
alter table public.workout_templates enable row level security;
alter table public.template_exercises enable row level security;
alter table public.workout_logs enable row level security;
alter table public.set_logs enable row level security;

drop policy if exists allow_authenticated_exercise_select on public.exercises;
drop policy if exists workout_templates_select_own on public.workout_templates;
drop policy if exists workout_templates_insert_own on public.workout_templates;
drop policy if exists workout_templates_update_own on public.workout_templates;
drop policy if exists workout_templates_delete_own on public.workout_templates;
drop policy if exists template_exercises_select_own on public.template_exercises;
drop policy if exists template_exercises_insert_own on public.template_exercises;
drop policy if exists template_exercises_update_own on public.template_exercises;
drop policy if exists template_exercises_delete_own on public.template_exercises;
drop policy if exists workout_logs_select_own on public.workout_logs;
drop policy if exists workout_logs_insert_own on public.workout_logs;
drop policy if exists workout_logs_update_own on public.workout_logs;
drop policy if exists workout_logs_delete_own on public.workout_logs;
drop policy if exists set_logs_select_own on public.set_logs;
drop policy if exists set_logs_insert_own on public.set_logs;
drop policy if exists set_logs_update_own on public.set_logs;
drop policy if exists set_logs_delete_own on public.set_logs;

create policy allow_authenticated_exercise_select
    on public.exercises
    for select
    to authenticated
    using (true);

create policy workout_templates_select_own
    on public.workout_templates
    for select
    to authenticated
    using (user_id = auth.uid());

create policy workout_templates_insert_own
    on public.workout_templates
    for insert
    to authenticated
    with check (user_id = auth.uid());

create policy workout_templates_update_own
    on public.workout_templates
    for update
    to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

create policy workout_templates_delete_own
    on public.workout_templates
    for delete
    to authenticated
    using (user_id = auth.uid());

create policy template_exercises_select_own
    on public.template_exercises
    for select
    to authenticated
    using (
        exists (
            select 1
            from public.workout_templates wt
            where wt.id = template_exercises.template_id
              and wt.user_id = auth.uid()
        )
    );

create policy template_exercises_insert_own
    on public.template_exercises
    for insert
    to authenticated
    with check (
        exists (
            select 1
            from public.workout_templates wt
            where wt.id = template_exercises.template_id
              and wt.user_id = auth.uid()
        )
    );

create policy template_exercises_update_own
    on public.template_exercises
    for update
    to authenticated
    using (
        exists (
            select 1
            from public.workout_templates wt
            where wt.id = template_exercises.template_id
              and wt.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from public.workout_templates wt
            where wt.id = template_exercises.template_id
              and wt.user_id = auth.uid()
        )
    );

create policy template_exercises_delete_own
    on public.template_exercises
    for delete
    to authenticated
    using (
        exists (
            select 1
            from public.workout_templates wt
            where wt.id = template_exercises.template_id
              and wt.user_id = auth.uid()
        )
    );

create policy workout_logs_select_own
    on public.workout_logs
    for select
    to authenticated
    using (user_id = auth.uid());

create policy workout_logs_insert_own
    on public.workout_logs
    for insert
    to authenticated
    with check (user_id = auth.uid());

create policy workout_logs_update_own
    on public.workout_logs
    for update
    to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

create policy workout_logs_delete_own
    on public.workout_logs
    for delete
    to authenticated
    using (user_id = auth.uid());

create policy set_logs_select_own
    on public.set_logs
    for select
    to authenticated
    using (
        exists (
            select 1
            from public.workout_logs wl
            where wl.id = set_logs.workout_log_id
              and wl.user_id = auth.uid()
        )
    );

create policy set_logs_insert_own
    on public.set_logs
    for insert
    to authenticated
    with check (
        exists (
            select 1
            from public.workout_logs wl
            where wl.id = set_logs.workout_log_id
              and wl.user_id = auth.uid()
        )
    );

create policy set_logs_update_own
    on public.set_logs
    for update
    to authenticated
    using (
        exists (
            select 1
            from public.workout_logs wl
            where wl.id = set_logs.workout_log_id
              and wl.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from public.workout_logs wl
            where wl.id = set_logs.workout_log_id
              and wl.user_id = auth.uid()
        )
    );

create policy set_logs_delete_own
    on public.set_logs
    for delete
    to authenticated
    using (
        exists (
            select 1
            from public.workout_logs wl
            where wl.id = set_logs.workout_log_id
              and wl.user_id = auth.uid()
        )
    );
