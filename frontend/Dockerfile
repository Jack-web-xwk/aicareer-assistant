# AI Career Assistant - Frontend (Nginx)
FROM docker.1ms.run/library/node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-cache
COPY . .
RUN npm run build

# Production: Nginx serve static files
FROM docker.1ms.run/library/nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
