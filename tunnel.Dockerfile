# autossh sidecar — baked so the tunnel doesn't apk-add on every start
# (no network dependency at boot, faster restarts). The key decode + autossh
# invocation stay in docker-compose.yml's command (they need runtime env).
FROM alpine:3.20
RUN apk add --no-cache autossh openssh-client
