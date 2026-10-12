# ==========================================
# Dockerfile do Front-end (Angular) do LMS RPA Monitor
# Estágio 1: build com Node · Estágio 2: arquivos estáticos servidos pelo Nginx
# ==========================================

# ---------- Build ----------
FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
# Configuração "production" (padrão): usa environment.ts → apiUrl '/api' e useMocks false
RUN npx ng build --configuration production

# ---------- Runtime ----------
FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
