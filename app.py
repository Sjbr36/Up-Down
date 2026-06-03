import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Dict, List
from database import (
    fetch_exercise_catalog,
    fetch_templates,
    fetch_template_exercises,
    insert_template,
    save_template_exercises,
    fetch_recent_set_weight,
    create_workout_log,
    create_set_logs,
)
from strava import create_strava_activity, build_strava_description
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Weightlifting Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY_BUTTON_STYLE = "background-color:#0f4c81;color:white;border-radius:8px;padding:0.7rem 1rem;font-weight:bold;"
SECONDARY_PANEL_STYLE = "background-color:#f7f9fc;border:1px solid #e1e6ef;border-radius:12px;padding:18px;margin-bottom:18px;"


def init_session_state() -> None:
    if "builder_exercise_config" not in st.session_state:
        st.session_state["builder_exercise_config"] = {}
    if "current_workout" not in st.session_state:
        st.session_state["current_workout"] = {}
    if "active_template_id" not in st.session_state:
        st.session_state["active_template_id"] = None


def render_timer_component(duration_seconds: int) -> None:
    html = """
    <div style="font-family:Arial, sans-serif; width:100%; padding:14px; border:1px solid #d0d7e7; border-radius:16px; background:#ffffff; text-align:center;">
      <div style="font-size:16px; color:#0f4c81; font-weight:700; margin-bottom:8px;">Timer</div>
      <div id="stage" style="font-size:15px; color:#475569; margin-bottom:6px;">Ready</div>
      <div id="display" style="font-size:42px; font-weight:800; color:#111827; margin-bottom:8px;">{duration}</div>
      <button id="start" style="{style}">Start Count-In</button>
      <div style="margin-top:10px; font-size:13px; color:#475569;">5s prep · {duration}s work · 5s finish</div>
    </div>
    <script>
      const display = document.getElementById('display');
      const stage = document.getElementById('stage');
      const startButton = document.getElementById('start');
      const baseline = {duration};
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

      function playBeep() {{
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.5);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
      }}

      function formatTime(seconds) {{
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return secs < 10 ? `{{mins}}:0{{secs}}` : `{{mins}}:{{secs}}`;
      }}

      async function runTimer() {{
        startButton.disabled = true;
        stage.textContent = 'Get Ready';
        let value = 5;
        while (value > 0) {{
          display.textContent = value;
          await new Promise(resolve => setTimeout(resolve, 1000));
          value -= 1;
        }}
        stage.textContent = 'Go';
        value = baseline;
        while (value > 0) {{
          display.textContent = formatTime(value);
          await new Promise(resolve => setTimeout(resolve, 1000));
          value -= 1;
        }}
        stage.textContent = 'Finish Warning';
        value = 5;
        while (value > 0) {{
          display.textContent = value;
          await new Promise(resolve => setTimeout(resolve, 1000));
          value -= 1;
        }}
        playBeep();
        display.textContent = formatTime(baseline);
        stage.textContent = 'Ready';
        startButton.disabled = false;
      }}

      startButton.addEventListener('click', runTimer);
    </script>
    """.format(duration=duration_seconds, style=PRIMARY_BUTTON_STYLE)
    components.html(html, height=260, scrolling=False)


def render_builder_page() -> None:
    st.markdown("## Workout Builder")
    st.markdown("Design reusable templates with group-based exercise selection and clean workout structure.")
    exercises = fetch_exercise_catalog()
    groups = sorted({exercise["primary_muscle_group"] for exercise in exercises})
    grouped = {group: [e for e in exercises if e["primary_muscle_group"] == group] for group in groups}

    with st.form("template_builder", clear_on_submit=False):
        template_name = st.text_input("Template name", max_chars=60)
        description = st.text_area("Description", help="Add workout goals or focus notes.")

        selected_exercises = []
        for group, items in grouped.items():
            with st.expander(group, expanded=False):
                choices = [f"{item['name']} ({item['category']})" for item in items]
                selected = st.multiselect(f"Select {group} exercises", choices, key=f"builder_{group}")
                if selected:
                    selected_exercises.extend([item for item in items if f"{item['name']} ({item['category']})" in selected])

        st.markdown("---")
        if selected_exercises:
            st.markdown("### Configure selected exercises")
            for exercise in selected_exercises:
                col1, col2, col3 = st.columns([2,1,1])
                col1.markdown(f"**{exercise['name']}** \n_{exercise['category']}_")
                default_sets = st.number_input(f"Sets for {exercise['name']}", min_value=1, max_value=10, value=3, key=f"sets_{exercise['id']}")
                if exercise['category'].lower() == 'timed':
                    default_duration = st.number_input(f"Duration (sec) for {exercise['name']}", min_value=10, max_value=600, value=45, step=5, key=f"duration_{exercise['id']}")
                    st.session_state["builder_exercise_config"][exercise['id']] = {
                        "default_sets": default_sets,
                        "default_reps": None,
                        "default_duration_seconds": default_duration,
                    }
                else:
                    default_reps = st.number_input(f"Reps for {exercise['name']}", min_value=1, max_value=30, value=8, key=f"reps_{exercise['id']}")
                    st.session_state["builder_exercise_config"][exercise['id']] = {
                        "default_sets": default_sets,
                        "default_reps": default_reps,
                        "default_duration_seconds": None,
                    }

        submitted = st.form_submit_button("Save Template")

        if submitted:
            if not template_name:
                st.warning("Enter a template name before saving.")
            elif not selected_exercises:
                st.warning("Select at least one exercise for the workout.")
            else:
                template = insert_template(template_name, description or "")
                if template:
                    exercise_rows = []
                    for exercise in selected_exercises:
                        config = st.session_state["builder_exercise_config"].get(exercise["id"])
                        exercise_rows.append({
                            "exercise_id": exercise["id"],
                            "default_sets": config["default_sets"],
                            "default_reps": config.get("default_reps"),
                            "default_duration_seconds": config.get("default_duration_seconds"),
                        })
                    if save_template_exercises(template["id"], exercise_rows):
                        st.success("Template saved successfully.")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to save the workout template.")
                else:
                    st.error("Failed to create workout template.")


def build_workout_state(template_id: str) -> Dict[str, Any]:
    template_exercises = fetch_template_exercises(template_id)
    exercise_catalog = {e["id"]: e for e in fetch_exercise_catalog()}
    workout_exercises = []
    for row in template_exercises:
        exercise = exercise_catalog.get(row["exercise_id"])
        if not exercise:
            continue
        last_weight = fetch_recent_set_weight(exercise["id"])
        row_sets = []
        for set_number in range(1, row["default_sets"] + 1):
            row_sets.append({
                "set_number": set_number,
                "weight_lbs": float(last_weight) if exercise["category"].lower() != "bodyweight" and exercise["category"].lower() != "timed" else 0,
                "reps_completed": row.get("default_reps") or 0,
                "duration_actual_seconds": row.get("default_duration_seconds") or 0,
                "is_completed": False,
            })
        workout_exercises.append({
            "exercise_id": exercise["id"],
            "name": exercise["name"],
            "category": exercise["category"],
            "primary_muscle_group": exercise["primary_muscle_group"],
            "target_sets": row["default_sets"],
            "target_reps": row.get("default_reps"),
            "target_duration_seconds": row.get("default_duration_seconds"),
            "sets": row_sets,
        })
    return {
        "template_id": template_id,
        "template_name": next((t["name"] for t in fetch_templates() if t["id"] == template_id), "Workout"),
        "start_time": datetime.now().isoformat(),
        "exercises": workout_exercises,
    }


def adjust_set_value(exercise_index: int, set_index: int, field: str, delta: int, min_value: int = 0) -> None:
    current = st.session_state["current_workout"]["exercises"][exercise_index]["sets"][set_index]
    current[field] = max(min_value, int(current.get(field, 0) or 0) + delta)


def toggle_set_complete(exercise_index: int, set_index: int) -> None:
    current = st.session_state["current_workout"]["exercises"][exercise_index]["sets"][set_index]
    current["is_completed"] = not current["is_completed"]


def render_workout_logger() -> None:
    st.markdown("## Workout Logger")
    st.markdown("Start a template and track every set with one-tap controls.")
    templates = fetch_templates()
    if not templates:
        st.info("Create a workout template first in the Workout Builder.")
        return
    template_map = {template["name"]: template for template in templates}
    selected_template_name = st.selectbox("Choose a saved template", list(template_map.keys()))
    selected_template = template_map[selected_template_name]

    if st.button("Start Workout", key="start_workout"):
        st.session_state["current_workout"] = build_workout_state(selected_template["id"])
        st.session_state["active_template_id"] = selected_template["id"]
        st.experimental_rerun()

    current_workout = st.session_state.get("current_workout")
    if not current_workout or current_workout.get("template_id") != selected_template["id"]:
        return

    st.markdown(f"### {current_workout['template_name']} | Started at {datetime.fromisoformat(current_workout['start_time']).strftime('%H:%M:%S')}")

    for exercise_index, exercise in enumerate(current_workout["exercises"]):
        with st.container():
            st.markdown(f"<div style='{SECONDARY_PANEL_STYLE}'> <strong>{exercise['name']}</strong> — {exercise['category']} | {exercise['primary_muscle_group']}</div>", unsafe_allow_html=True)
            for set_index, set_state in enumerate(exercise["sets"]):
                row = st.columns([1, 3, 3, 1])
                row[0].markdown(f"**Set {set_state['set_number']}**")

                if exercise["category"].lower() == "timed":
                    timer_container = row[1].empty()
                    with timer_container:
                        render_timer_component(exercise["target_duration_seconds"] or 45)
                    duration_cols = row[2].columns([1,1,1])
                    duration_cols[0].button("-5s", key=f"duration_minus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"duration_actual_seconds","delta":-5,"min_value":0})
                    duration_cols[1].markdown(f"{set_state['duration_actual_seconds']} sec")
                    duration_cols[2].button("+5s", key=f"duration_plus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"duration_actual_seconds","delta":5,"min_value":0})
                else:
                    weight_cols = row[1].columns([1,1,1])
                    if exercise["category"].lower() != "bodyweight":
                        weight_cols[0].button("-5 lbs", key=f"weight_minus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"weight_lbs","delta":-5,"min_value":0})
                        weight_cols[1].button(f"{int(set_state['weight_lbs'])} lbs", key=f"weight_display_{exercise_index}_{set_index}")
                        weight_cols[2].button("+5 lbs", key=f"weight_plus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"weight_lbs","delta":5,"min_value":0})
                    else:
                        row[1].markdown("Bodyweight exercise — weight tracking hidden.")

                    rep_cols = row[2].columns([1,1,1])
                    rep_cols[0].button("-1", key=f"rep_minus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"reps_completed","delta":-1,"min_value":0})
                    rep_cols[1].markdown(f"{set_state['reps_completed']} reps")
                    rep_cols[2].button("+1", key=f"rep_plus_{exercise_index}_{set_index}", on_click=adjust_set_value, kwargs={"exercise_index":exercise_index,"set_index":set_index,"field":"reps_completed","delta":1,"min_value":0})

                completed_label = "Completed" if set_state["is_completed"] else "Mark Done"
                row[3].button(completed_label, key=f"complete_{exercise_index}_{set_index}", on_click=toggle_set_complete, kwargs={"exercise_index":exercise_index,"set_index":set_index})

    if st.button("Finish Workout", key="finish_workout"):
        finish_workout(current_workout)


def finish_workout(current_workout: Dict[str, Any]) -> None:
    start_time = datetime.fromisoformat(current_workout["start_time"])
    end_time = datetime.now()
    total_minutes = round((end_time - start_time).total_seconds() / 60, 2)
    focus_areas = sorted({exercise["primary_muscle_group"] for exercise in current_workout["exercises"]})
    total_volume = 0.0
    set_entries = []
    for exercise in current_workout["exercises"]:
        for set_state in exercise["sets"]:
            if exercise["category"].lower() not in ["timed"]:
                total_volume += float(set_state.get("weight_lbs", 0)) * int(set_state.get("reps_completed", 0))
            set_entries.append({
                "exercise_id": exercise["exercise_id"],
                "set_number": set_state["set_number"],
                "weight_lbs": set_state.get("weight_lbs", 0),
                "reps_completed": set_state.get("reps_completed", 0),
                "duration_actual_seconds": set_state.get("duration_actual_seconds", 0),
                "is_completed": set_state.get("is_completed", False),
            })

    perceived_effort = st.slider("Perceived Level of Effort", min_value=1, max_value=10, value=7)
    summary = build_strava_description(current_workout["template_name"], total_minutes, focus_areas, total_volume, perceived_effort)
    st.markdown("### Workout Summary")
    st.markdown(f"**Duration:** {total_minutes} mins")
    st.markdown(f"**Focus Areas:** {', '.join(focus_areas)}")
    st.markdown(f"**Total Volume:** {int(total_volume):,} lbs")
    st.markdown(f"**Effort:** {perceived_effort}/10")

    strava_response = None
    try:
        strava_response = create_strava_activity(
            current_workout["template_name"],
            summary,
            int(total_minutes * 60),
            start_time,
        )
    except Exception as exc:
        st.warning(f"Strava integration error: {exc}")

    strava_id = strava_response.get("id") if strava_response else None
    saved = create_workout_log(
        current_workout["template_id"],
        start_time,
        end_time,
        total_minutes,
        focus_areas,
        perceived_effort,
        total_volume,
        strava_id,
    )
    if saved:
        create_set_logs(saved["id"], set_entries)
        st.success("Workout saved successfully.")
        if strava_response:
            st.info(f"Strava activity created: ID {strava_id}")
        st.session_state["current_workout"] = {}
        st.session_state["active_template_id"] = None
        st.experimental_rerun()
    else:
        st.error("Unable to save workout to the database.")


def main() -> None:
    init_session_state()
    st.markdown("# Weightlifting Tracker")
    st.markdown("A clean, high-contrast workout builder and logging experience for the gym.")

    page = st.sidebar.selectbox("Navigation", ["Workout Builder", "Workout Logger"])
    if page == "Workout Builder":
        render_builder_page()
    else:
        render_workout_logger()

if __name__ == "__main__":
    main()
