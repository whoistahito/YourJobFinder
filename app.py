"""Production Flask entrypoint.

Thin bootstrap: builds the app via the factory (which owns all routes + the
matched-jobs API). The DB is reached over the network (the autossh sidecar in
prod), so there's no tunnel to start here. gunicorn targets `app:app`.
"""
from credential import DatabaseCredential
from infrastructure.app_factory import create_app

app = create_app(db_uri=DatabaseCredential.get_db_uri())


if __name__ == "__main__":
    app.run(threaded=True, port=5000)