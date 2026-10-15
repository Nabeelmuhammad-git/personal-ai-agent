import os

ASSISTANT_NAME = "ai nabeel"
BACKUP_PASSWORD = os.getenv("AI_NABEEL_BACKUP_PASSWORD", "nn22")


def validate_backup_password(password):
    return str(password or "").strip() == str(BACKUP_PASSWORD).strip()