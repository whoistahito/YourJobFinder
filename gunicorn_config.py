bind = "0.0.0.0:8080"
workers = 2
# gunicorn 25.x opens a control socket at /run/gunicorn.ctl by default; the
# non-root container user can't write there. We don't use gunicornc, so disable.
control_socket_disable = True
