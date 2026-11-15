# Multi-stage Dockerfile for Smart Quiz Frontend (React 18 + Vite)
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies with lockfile
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build production bundle
COPY . .
# Set default production API URL (relative path through reverse proxy)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: Serve static files with lightweight Nginx
FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
