# syntax=docker/dockerfile:1

# ── Build stage: compile the React app to static files ───────────────────────
# The output is plain HTML/JS/CSS, so it is built once on the build machine's
# own architecture even when the final image targets another one.
FROM --platform=$BUILDPLATFORM node:24-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build


# ── Runtime stage: nginx (unprivileged, listens on 8080) ─────────────────────
FROM nginxinc/nginx-unprivileged:1.31-alpine AS runtime

# Where nginx forwards /api/* requests. Overridden per environment.
ENV BACKEND_URL=http://backend:8000

# The image's entrypoint fills ${BACKEND_URL} into this template at start-up.
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
# nginx runs as a non-root user, so the template must be world-readable
# whatever permissions the file had on the machine that built it.
USER root
RUN chmod -R a+rX /etc/nginx/templates
USER nginx
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --start-interval=1s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
