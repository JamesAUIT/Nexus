# Cloud Nexus Web - Next.js
FROM node:20-alpine AS base
WORKDIR /app

# Dependencies
FROM base AS deps
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Build
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# Avoid OOM during webpack on small VMs; tune if needed
ENV NODE_OPTIONS="--max-old-space-size=6144"
RUN npm run build

# Runner — use built-in `node` user (uid 1000); avoid addgroup/adduser conflicting with base image GID 1000
FROM base AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
