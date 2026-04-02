# AI Career Assistant - Frontend (Nginx)
# Build context must be repository root (see docker-compose frontend.build).

FROM docker.1ms.run/library/node:20-alpine AS builder

RUN apk add --no-cache git python3

WORKDIR /repo
COPY frontend/package.json frontend/package-lock.json ./frontend/
WORKDIR /repo/frontend
RUN npm ci --no-cache
COPY frontend/ ./
WORKDIR /repo
COPY backend/scripts/sync_ai_daily.py backend/scripts/sync_ai_daily.py
RUN python3 backend/scripts/sync_ai_daily.py
WORKDIR /repo/frontend
RUN npx tsc && npx vite build

# Production: Nginx serve static files
FROM docker.1ms.run/library/nginx:1.27-alpine

COPY --from=builder /repo/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
