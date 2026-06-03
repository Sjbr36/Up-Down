-- Supabase / PostgreSQL schema for Weightlifting Tracker
create extension if not exists "pgcrypto";

create table if not exists exercises (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    category text not null,
    primary_muscle_group text not null,
    secondary_muscle_groups text[] default array[]::text[],
    created_at timestamptz not null default now()
);

create table if not exists workout_templates (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text,
    created_at timestamptz not null default now()
);

-- Create template_exercises with exercise_id typed to match exercises.id
DO $$
DECLARE
    _udt_name text;
    _exercise_id_type text;
BEGIN
    SELECT udt_name INTO _udt_name
      FROM information_schema.columns
     WHERE table_name = 'exercises' AND column_name = 'id'
     LIMIT 1;

    IF _udt_name IS NULL THEN
        -- exercises table doesn't exist yet; default to uuid
        _exercise_id_type := 'uuid';
    ELSIF _udt_name = 'int4' THEN
        _exercise_id_type := 'integer';
    ELSIF _udt_name = 'int8' THEN
        _exercise_id_type := 'bigint';
    ELSE
        _exercise_id_type := _udt_name;
    END IF;

    EXECUTE format($sql$
        create table if not exists template_exercises (
            id uuid primary key default gen_random_uuid(),
            template_id uuid not null references workout_templates(id) on delete cascade,
            exercise_id %s not null references exercises(id) on delete restrict,
            sequence_order int not null,
            default_sets int not null check (default_sets > 0),
            default_reps int,
            default_duration_seconds int,
            created_at timestamptz not null default now(),
            constraint default_target_check check ((default_reps is not null and default_duration_seconds is null) or (default_reps is null and default_duration_seconds is not null))
        );
    $sql$, _exercise_id_type);
END
$$;

create table if not exists workout_logs (
    id uuid primary key default gen_random_uuid(),
    template_id uuid not null references workout_templates(id) on delete set null,
    start_time timestamptz not null,
    end_time timestamptz not null,
    total_duration_minutes numeric(6,2) not null,
    focus_areas text[] default array[]::text[],
    perceived_effort int not null check (perceived_effort between 1 and 10),
    total_volume_lbs numeric(10,2) not null,
    strava_activity_id text,
    created_at timestamptz not null default now()
);

-- Create set_logs with exercise_id typed to match exercises.id
DO $$
DECLARE
    _udt_name text;
    _exercise_id_type text;
BEGIN
    SELECT udt_name INTO _udt_name
      FROM information_schema.columns
     WHERE table_name = 'exercises' AND column_name = 'id'
     LIMIT 1;

    IF _udt_name IS NULL THEN
        _exercise_id_type := 'uuid';
    ELSIF _udt_name = 'int4' THEN
        _exercise_id_type := 'integer';
    ELSIF _udt_name = 'int8' THEN
        _exercise_id_type := 'bigint';
    ELSE
        _exercise_id_type := _udt_name;
    END IF;

    EXECUTE format($sql$
        create table if not exists set_logs (
            id uuid primary key default gen_random_uuid(),
            workout_log_id uuid not null references workout_logs(id) on delete cascade,
            exercise_id %s not null references exercises(id) on delete restrict,
            set_number int not null,
            weight_lbs numeric(6,2) default 0,
            reps_completed int default 0,
            duration_actual_seconds int default 0,
            is_completed boolean not null default false,
            created_at timestamptz not null default now()
        );
    $sql$, _exercise_id_type);
END
$$;

create index if not exists idx_exercises_category on exercises(category);
create index if not exists idx_exercises_primary_muscle_group on exercises(primary_muscle_group);
create index if not exists idx_template_exercises_template_id on template_exercises(template_id);
create index if not exists idx_template_exercises_exercise_id on template_exercises(exercise_id);
create index if not exists idx_workout_logs_template_id on workout_logs(template_id);
create index if not exists idx_set_logs_workout_log_id on set_logs(workout_log_id);
create index if not exists idx_set_logs_exercise_id on set_logs(exercise_id);

-- Seed standard movements for a full movement library
insert into exercises (name, category, primary_muscle_group, secondary_muscle_groups) values
('Back Squat','Barbell','Quads',array['Glutes','Hamstrings']),
('Front Squat','Barbell','Quads',array['Glutes','Core']),
('Bench Press','Barbell','Chest',array['Triceps','Shoulders']),
('Overhead Press','Barbell','Shoulders',array['Triceps','Upper Back']),
('Deadlift','Barbell','Hamstrings',array['Glutes','Lower Back']),
('Romanian Deadlift','Barbell','Hamstrings',array['Glutes','Lower Back']),
('Bent-Over Row','Barbell','Back',array['Biceps','Rear Delts']),
('Pull-up','Bodyweight','Back',array['Biceps','Shoulders']),
('Chin-up','Bodyweight','Back',array['Biceps','Forearms']),
('Push-up','Bodyweight','Chest',array['Triceps','Shoulders']),
('Dip','Bodyweight','Chest',array['Triceps','Shoulders']),
('Walking Lunge','Bodyweight','Quads',array['Glutes','Hamstrings']),
('Bulgarian Split Squat','Dumbbell','Quads',array['Glutes','Hamstrings']),
('Dumbbell Bench Press','Dumbbell','Chest',array['Triceps','Shoulders']),
('Dumbbell Shoulder Press','Dumbbell','Shoulders',array['Triceps','Upper Back']),
('Dumbbell Row','Dumbbell','Back',array['Biceps','Lats']),
('Kettlebell Swing','Kettlebell','Hamstrings',array['Glutes','Core']),
('Goblet Squat','Kettlebell','Quads',array['Glutes','Core']),
('Kettlebell Clean','Kettlebell','Full Body',array['Shoulders','Back']),
('Plank','Bodyweight','Core',array['Shoulders','Glutes']),
('Hollow Hold','Bodyweight','Core',array['Abs','Hip Flexors']),
('Mountain Climbers','Bodyweight','Core',array['Cardio','Shoulders']),
('Farmer''s Carry','Dumbbell','Forearms',array['Shoulders','Core']),
('T-Bar Row','Barbell','Back',array['Biceps','Rear Delts']),
('Lat Pulldown','Cable','Back',array['Biceps','Shoulders']),
('Seated Cable Row','Cable','Back',array['Biceps','Rear Delts']),
('Glute Bridge','Barbell','Glutes',array['Hamstrings','Core']),
('Single-Leg Deadlift','Dumbbell','Hamstrings',array['Glutes','Core']),
('Box Jump','Bodyweight','Quads',array['Glutes','Calves']),
('Battle Ropes','Timed','Full Body',array['Shoulders','Cardio']),
('Rowing Machine','Timed','Full Body',array['Back','Cardio']),
('Stationary Bike','Timed','Full Body',array['Legs','Cardio']);
