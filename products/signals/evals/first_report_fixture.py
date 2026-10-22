from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import JsonValue

from posthog.dataclasses import frozen

BASELINE_VERSION = "2.8.0"
CURRENT_VERSION = "2.9.0"
UPLOAD_ERROR = "Upload request failed while preparing the file"
UPLOAD_FINGERPRINT = "upload-request-preparation"


@frozen
class UploadEvent:
    event: str
    distinct_id: str
    person_id: str
    timestamp: datetime
    properties: dict[str, JsonValue]


def upload_events(anchor: datetime, *, scenario: Literal["regression", "control", "sparse"]) -> list[UploadEvent]:
    events: list[UploadEvent] = []
    days = [2] if scenario == "sparse" else range(15, 1, -1)
    people_per_day = 2 if scenario == "sparse" else 100
    for days_ago in days:
        recent = days_ago <= 8
        for browser in ("Safari", "Chrome"):
            successful = 20 if scenario == "regression" and recent and browser == "Safari" else 80
            for index in range(people_per_day):
                distinct_id = f"desktop-{browser.lower()}-{days_ago}-{index}"
                person_id = str(uuid5(NAMESPACE_URL, distinct_id))
                timestamp = anchor - timedelta(days=days_ago) + timedelta(hours=9, minutes=index)
                properties: dict[str, JsonValue] = {
                    "$browser": browser,
                    "$os": "Mac OS X",
                    "$current_url": "https://hedgebox.example/files/",
                    "$lib": "web",
                    "app_version": CURRENT_VERSION if recent else BASELINE_VERSION,
                    "$session_id": str(uuid5(NAMESPACE_URL, f"session-{distinct_id}")),
                }
                events.append(
                    UploadEvent(
                        event="signed_up",
                        distinct_id=distinct_id,
                        person_id=person_id,
                        timestamp=timestamp,
                        properties={**properties, "from_invite": False},
                    )
                )
                if index < successful and scenario != "sparse":
                    events.append(
                        UploadEvent(
                            event="uploaded_file",
                            distinct_id=distinct_id,
                            person_id=person_id,
                            timestamp=timestamp + timedelta(minutes=10),
                            properties={**properties, "file_type": "image/png", "file_size_b": 2048, "used_mb": 2048},
                        )
                    )
                elif scenario == "regression" and recent and browser == "Safari":
                    events.append(
                        UploadEvent(
                            event="$exception",
                            distinct_id=distinct_id,
                            person_id=person_id,
                            timestamp=timestamp + timedelta(minutes=1),
                            properties=properties,
                        )
                    )
    return events
