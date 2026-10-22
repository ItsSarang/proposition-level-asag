# Stage 1: Build Vite React Application
FROM node:20-alpine AS build

LABEL maintainer="ASAG Research Team"
LABEL description="Proposition-Level ASAG Interactive Frontend Workbench"

WORKDIR /app

# Copy package manifests and install npm dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source files
COPY . .

# Optional build argument for remote API endpoint (e.g. EC2 backend public IP)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Build static bundle
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine

# Copy compiled static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
