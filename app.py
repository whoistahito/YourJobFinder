"""Production Flask entrypoint.

Thin bootstrap: starts the SSH tunnel to the DB, builds the app via the
factory (which owns all routes + the matched-jobs API). gunicorn targets
`app:app`.
"""
from credential import DatabaseCredential
from extension import db
from infrastructure.app_factory import create_app
from ssh_tunnel import start_ssh_tunnel

start_ssh_tunnel()
app = create_app(db_uri=DatabaseCredential.get_db_uri())


if __name__ == "__main__":
    app.run(threaded=True, port=5000)