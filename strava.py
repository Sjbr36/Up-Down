import streamlit as st
import requests
from datetime import datetime
from typing import Optional

STRAVA_API_URL = "https://www.strava.com/api/v3/activities"


def get_strava_token() -> Optional[str]:
    strava_config = st.secrets.get("strava") or {}
    return strava_config.get("access_token")


def create_strava_activity(name: str, description: str, elapsed_seconds: int, start_time: datetime) -> Optional[dict]:
    access_token = get_strava_token()
    if not access_token:
        return None

    payload = {
        "name": name,
        "description": description,
        "elapsed_time": elapsed_seconds,
        "start_date_local": start_time.isoformat(),
        "sport_type": "WeightTraining",
        "trainer": False,
        "commute": False,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(STRAVA_API_URL, headers=headers, data=payload, timeout=20)
    if response.ok:
        return response.json()
    st.warning(f"Strava upload failed: {response.status_code} {response.text}")
    return None


def build_strava_description(
    template_name: str,
    total_minutes: float,
    focus_areas: list,
    total_volume: float,
    effort: int,
) -> str:
    focus_text = ", ".join(focus_areas) if focus_areas else "General Strength"
    return (
        f"{template_name}: {int(total_minutes)} mins. Focused on {focus_text}. "
        f"Total Volume: {int(total_volume):,} lbs. Effort: {effort}/10."
    )
