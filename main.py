"""Worker entrypoint — one notify pass over confirmed users, then exit.

Not a resident loop anymore: the platform runs this on a schedule (Coolify
scheduled task → `python main.py`). Confirmation emails are sent in-request at
signup (see infrastructure/app_factory.py), so there's no polling here.
"""
from app import app
from notifications import notify_all_confirmed_users

if __name__ == "__main__":
    with app.app_context():
        notify_all_confirmed_users()
