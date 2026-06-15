# Stage 1: Build the React application
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine
# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*
# Copy built assets from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy the nginx configuration template
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Substitute ONLY the $PORT variable into the nginx config at runtime
CMD envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'
