# Build from the repository root so the pnpm workspace lockfile is available:
#   docker build -f frontend/Dockerfile .
FROM node:24-alpine AS base
RUN npm install -g pnpm@10.33.1

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json frontend/
COPY shared shared/
RUN pnpm install --frozen-lockfile --filter null-frontend...

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/frontend/node_modules ./frontend/node_modules
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY shared shared/
COPY frontend frontend/
# NEXT_PUBLIC_* values are inlined at build time and must be reachable from
# the user's browser, not from inside the Docker network.
ARG NEXT_PUBLIC_API_URL=http://localhost:3301
ARG NEXT_PUBLIC_WS_URL=ws://localhost:3301
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
RUN pnpm --filter null-frontend build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=builder /app/frontend/public ./frontend/public

EXPOSE 3000
CMD ["node", "frontend/server.js"]
