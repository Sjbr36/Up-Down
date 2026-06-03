import streamlit as st
from supabase import create_client, Client
from datetime import datetime
from typing import Any, Dict, List, Optional


def get_supabase_client() -> Client:
    url = st.secrets.get("supabase_url")
    key = st.secrets.get("supabase_key")
    if not url or not key:
        st.error("Supabase connection secrets are missing. Please set supabase_url and supabase_key in Streamlit secrets.")
        st.stop()
    return create_client(url, key)


def fetch_exercise_catalog() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    resp = supabase.table("exercises").select("*").order("primary_muscle_group").order("name").execute()
    return resp.data or []


def fetch_templates() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    resp = supabase.table("workout_templates").select("*").order("created_at", desc=True).execute()
    return resp.data or []


def fetch_template_exercises(template_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    resp = supabase.table("template_exercises").select("*").eq("template_id", template_id).order("sequence_order").execute()
    return resp.data or []


def insert_template(name: str, description: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    payload = {
        "name": name,
        "description": description,
    }
    resp = supabase.table("workout_templates").insert(payload).select("*").single().execute()
    return resp.data if resp.error is None else None


def save_template_exercises(template_id: str, exercise_rows: List[Dict[str, Any]]) -> bool:
    supabase = get_supabase_client()
    payload = []
    for idx, row in enumerate(exercise_rows, start=1):
        payload.append({
            "template_id": template_id,
            "exercise_id": row["exercise_id"],
            "sequence_order": idx,
            "default_sets": row["default_sets"],
            "default_reps": row.get("default_reps"),
            "default_duration_seconds": row.get("default_duration_seconds"),
        })
    resp = supabase.table("template_exercises").insert(payload).execute()
    return resp.error is None


def fetch_recent_set_weight(exercise_id: str) -> float:
    supabase = get_supabase_client()
    resp = supabase.table("set_logs").select("weight_lbs").eq("exercise_id", exercise_id).order("created_at", desc=True).limit(1).execute()
    data = resp.data or []
    if data:
        return float(data[0].get("weight_lbs", 0) or 0)
    return 0.0


def create_workout_log(template_id: str, start_time: datetime, end_time: datetime, total_duration_minutes: float, focus_areas: List[str], perceived_effort: int, total_volume_lbs: float, strava_activity_id: Optional[str]) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    payload = {
        "template_id": template_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_minutes": total_duration_minutes,
        "focus_areas": focus_areas,
        "perceived_effort": perceived_effort,
        "total_volume_lbs": total_volume_lbs,
        "strava_activity_id": strava_activity_id,
    }
    resp = supabase.table("workout_logs").insert(payload).select("*").single().execute()
    return resp.data if resp.error is None else None


def create_set_logs(workout_log_id: str, set_entries: List[Dict[str, Any]]) -> bool:
    supabase = get_supabase_client()
    payload = []
    for entry in set_entries:
        payload.append({
            "workout_log_id": workout_log_id,
            "exercise_id": entry["exercise_id"],
            "set_number": entry["set_number"],
            "weight_lbs": entry.get("weight_lbs", 0),
            "reps_completed": entry.get("reps_completed", 0),
            "duration_actual_seconds": entry.get("duration_actual_seconds", 0),
            "is_completed": entry.get("is_completed", False),
        })
    resp = supabase.table("set_logs").insert(payload).execute()
    return resp.error is None
