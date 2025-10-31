# ==================== Base Stage ====================
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY apps/ui/package.json apps/ui/package-lock.json* ./

# Install dependencies
RUN npm ci

# ==================== Development Stage ====================
FROM base AS development
WORKDIR /app

# Install dependencies
RUN apk add --no-cache libc6-compat

# Copy package files and install
COPY apps/ui/package.json apps/ui/package-lock.json* ./
RUN npm ci

# Download sample data
RUN mkdir -p scripts
COPY apps/ui/scripts/download-sample-data.mjs ./scripts/
RUN node scripts/download-sample-data.mjs || echo "Warning: Failed to download sample data, will be downloaded at runtime"

# Copy README.md from root for docs page
COPY README.md /README.md

# Expose port
EXPOSE 3000

ENV NODE_ENV=development
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Run dev server with volume mounts from docker-compose
CMD ["npm", "run", "dev"]

# ==================== Builder Stage ====================
FROM base AS builder
WORKDIR /app

# Accept build arguments for Next.js public environment variables
ARG NEXT_PUBLIC_API_URL=http://api.pierrestack.com
ARG NEXT_PUBLIC_API_DOCS_URL=http://api.pierrestack.com/docs
ARG NEXT_PUBLIC_TEMPORAL_UI_HOST=http://temporal.pierrestack.com
ARG NEXT_PUBLIC_RABBITMQ_UI_HOST=http://rabbitmq.pierrestack.com
ARG NEXT_PUBLIC_DATABASE_UI_HOST=http://db.pierrestack.com

# Set them as environment variables for the build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_DOCS_URL=$NEXT_PUBLIC_API_DOCS_URL
ENV NEXT_PUBLIC_TEMPORAL_UI_HOST=$NEXT_PUBLIC_TEMPORAL_UI_HOST
ENV NEXT_PUBLIC_RABBITMQ_UI_HOST=$NEXT_PUBLIC_RABBITMQ_UI_HOST
ENV NEXT_PUBLIC_DATABASE_UI_HOST=$NEXT_PUBLIC_DATABASE_UI_HOST

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY apps/ui/ .

# Download sample data before build (commented out - script doesn't exist)
# RUN node scripts/download-sample-data.mjs

# Copy README.md from root for docs page
COPY README.md /README.md

# Build Next.js application
RUN npm run build

# ==================== Runner Stage ====================
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy cached sample data
COPY --from=builder --chown=nextjs:nodejs /app/.cache ./.cache

# Copy README.md for docs page
COPY --from=builder /README.md /README.md

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
