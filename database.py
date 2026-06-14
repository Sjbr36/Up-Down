import streamlit as st
from supabase import create_client, Client
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional


def _execute_write(builder: Any) -> Optional[Any]:
    try:
        return builder.execute()
    except Exception as exc:
        st.warning(f"Database write failed: {exc}")
        return None


def _first_response_row(resp: Any) -> Optional[Dict[str, Any]]:
    data = getattr(resp, "data", None) or []
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


def get_supabase_client(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> Client:
    url = st.secrets.get("supabase_url")
    key = st.secrets.get("supabase_key")
    if not url or not key:
        st.error("Supabase connection secrets are missing. Please set supabase_url and supabase_key in Streamlit secrets.")
        st.stop()

    client = create_client(url, key)
    if access_token:
        try:
            client.auth.set_session(access_token, refresh_token or "")
        except Exception:
            pass
    return client


def sign_in_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    try:
        resp = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception as exc:
        st.warning(f"Sign in failed: {exc}")
        return None

    if isinstance(resp, dict):
        session = resp.get("session")
        user = resp.get("user")
    else:
        session = getattr(resp, "session", None)
        user = getattr(resp, "user", None)
    if not session or not user:
        return None

    if isinstance(session, dict):
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
    else:
        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

    if isinstance(user, dict):
        user_id = user.get("id")
        user_email = user.get("email", email)
    else:
        user_id = getattr(user, "id", None)
        user_email = getattr(user, "email", email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "email": user_email,
        },
    }


def sign_out_user(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> None:
    supabase = get_supabase_client(access_token, refresh_token)
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def parse_password_reset_params(raw_params: Optional[Mapping[str, Any]] = None) -> Dict[str, Optional[str]]:
    params = dict(raw_params or {})
    token_hash = params.get("token_hash") or params.get("token") or params.get("access_token")
    recovery_type = params.get("type") or ("recovery" if token_hash else None)
    return {
        "token_hash": token_hash,
        "type": recovery_type,
    }


def complete_password_reset(
    new_password: str,
    token_hash: Optional[str] = None,
    recovery_type: str = "recovery",
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> bool:
    if not new_password or not token_hash:
        return False

    supabase = get_supabase_client(access_token, refresh_token)
    try:
        verify_params = {
            "token_hash": token_hash,
            "type": recovery_type,
            "password": new_password,
        }
        resp = supabase.auth.verify_otp(verify_params)
    except Exception as exc:
        st.warning(f"Password reset verification failed: {exc}")
        return False

    if getattr(resp, "session", None):
        return True

    try:
        update_resp = supabase.auth.update_user({"password": new_password})
        return bool(getattr(update_resp, "user", None) or getattr(update_resp, "data", None))
    except Exception as exc:
        st.warning(f"Password update failed: {exc}")
        return False


def request_password_reset(email: str, access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> bool:
    if not email:
        return False

    supabase = get_supabase_client(access_token, refresh_token)
    normalized_email = email.strip()
    reset_options = None

    try:
        redirect_to = st.secrets.get("password_reset_redirect_to")
        if redirect_to:
            reset_options = {"redirect_to": redirect_to}
    except Exception:
        pass

    try:
        supabase.auth.reset_password_for_email(normalized_email, reset_options)
        return True
    except Exception as exc:
        st.warning(f"Password reset request failed: {exc}")
        return False


def fetch_exercise_catalog(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> List[Dict[str, Any]]:
    supabase = get_supabase_client(access_token, refresh_token)
    resp = supabase.table("exercises").select("*").order("primary_muscle_group").order("name").execute()
    return resp.data or []


def fetch_templates(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> List[Dict[str, Any]]:
    supabase = get_supabase_client(access_token, refresh_token)
    resp = supabase.table("workout_templates").select("*").order("created_at", desc=True).execute()
    return resp.data or []


def fetch_template_exercises(template_id: str, access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> List[Dict[str, Any]]:
    supabase = get_supabase_client(access_token, refresh_token)
    resp = supabase.table("template_exercises").select("*").eq("template_id", template_id).order("sequence_order").execute()
    return resp.data or []


def insert_template(name: str, description: str, user_id: str, access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client(access_token, refresh_token)
    payload = {
        "name": name,
        "description": description,
        "user_id": user_id,
    }
    resp = _execute_write(supabase.table("workout_templates").insert(payload).select("*"))
    return _first_response_row(resp)


def save_template_exercises(template_id: str, exercise_rows: List[Dict[str, Any]], access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> bool:
    supabase = get_supabase_client(access_token, refresh_token)
    payload = []
    for idx, row in enumerate(exercise_rows, start=1):
        payload.append({
            "template_id": template_id,
            "exercise_id": row["exercise_id"],
            "sequence_order": idx,
            "default_sets": row["default_sets"],
            "default_reps": row.get("default_reps"),
            "default_duration_seconds": row.get("default_duration_seconds"),
            "superset_group": row.get("superset_group"),
            "superset_order": row.get("superset_order"),
        })
    resp = _execute_write(supabase.table("template_exercises").insert(payload))
    return resp is not None


def fetch_recent_set_weight(
    exercise_id: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> float:
    supabase = get_supabase_client(access_token, refresh_token)
    resp = (
        supabase.table("set_logs")
        .select("weight_lbs")
        .eq("exercise_id", exercise_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = resp.data or []
    if data:
        return float(data[0].get("weight_lbs", 0) or 0)
    return 0.0


def create_workout_log(
    template_id: str,
    start_time: datetime,
    end_time: datetime,
    total_duration_minutes: float,
    focus_areas: List[str],
    perceived_effort: int,
    total_volume_lbs: float,
    strava_activity_id: Optional[str],
    user_id: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client(access_token, refresh_token)
    payload = {
        "user_id": user_id,
        "template_id": template_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_minutes": total_duration_minutes,
        "focus_areas": focus_areas,
        "perceived_effort": perceived_effort,
        "total_volume_lbs": total_volume_lbs,
        "strava_activity_id": strava_activity_id,
    }
    resp = _execute_write(supabase.table("workout_logs").insert(payload).select("*"))
    return _first_response_row(resp)


def create_set_logs(
    workout_log_id: str,
    set_entries: List[Dict[str, Any]],
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> bool:
    supabase = get_supabase_client(access_token, refresh_token)
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
    resp = _execute_write(supabase.table("set_logs").insert(payload))
    return resp is not None
