import atexit
import base64
import os

SSH_DB_PORT = int(os.environ.get("ssh_db_port"))

SSH_DB_HOST = os.environ.get("ssh_db_host")

SSH_USERNAME = os.environ.get("ssh_user", "root")

SSH_PORT = int(os.environ.get("ssh_port", "22"))

SSH_PRIVATE_KEY = os.environ.get("ssh_private_key")
SSH_HOST = os.environ.get("ssh_host")
import tempfile

from sshtunnel import SSHTunnelForwarder

_tunnel: SSHTunnelForwarder | None = None
_key_file_path: str | None = None


def get_tunnel() -> SSHTunnelForwarder | None:
    return _tunnel


def start_ssh_tunnel() -> SSHTunnelForwarder | None:
    """
    Start an SSH tunnel to the database server if ssh_host is configured.
    The tunnel forwards a local port to the remote DB port.
    Returns the tunnel (or None if SSH is not configured).
    """
    global _tunnel, _key_file_path
    pkey_path = None
    private_key_b64 = SSH_PRIVATE_KEY
    if private_key_b64:
        key_data = base64.b64decode(private_key_b64)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tmp.write(key_data)
        tmp.close()
        os.chmod(tmp.name, 0o600)
        _key_file_path = tmp.name
        pkey_path = tmp.name
        atexit.register(_cleanup_key_file)

    try:
        _tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USERNAME,
            ssh_pkey=pkey_path,
            remote_bind_address=(SSH_DB_HOST, SSH_DB_PORT),
            set_keepalive=30,
        )
        _tunnel.start()
        atexit.register(_tunnel.stop)
    except Exception as e:
        print(f"[ssh_tunnel] WARNING: Failed to start SSH tunnel: {e}")
        _tunnel = None
    return _tunnel


def _cleanup_key_file():
    if _key_file_path and os.path.exists(_key_file_path):
        os.unlink(_key_file_path)
