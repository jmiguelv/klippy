# Build stage
FROM node:22-slim AS build

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --no-engine-strict

# Copy source code
COPY . .

# Build the application (SSG)
RUN pnpm build

# Production stage
FROM nginx:alpine

# Copy built static files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Optional: Add custom nginx config if needed for SPA routing/trailing slashes
# For SSG with trailing slashes, default nginx should work fine

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
