import os
from googleapiclient.discovery import build

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]
SCHEDULER_JOB_ID = os.environ["SCHEDULER_JOB_ID"]


def _job_name() -> str:
    return f"projects/{PROJECT_ID}/locations/{REGION}/jobs/{SCHEDULER_JOB_ID}"


def pause_scheduler_job() -> None:
    service = build("cloudscheduler", "v1")
    service.projects().locations().jobs().pause(
        name=_job_name()
    ).execute()


def resume_scheduler_job() -> None:
    service = build("cloudscheduler", "v1")
    service.projects().locations().jobs().resume(
        name=_job_name()
    ).execute()