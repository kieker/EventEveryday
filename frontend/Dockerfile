FROM node:24-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci && sha256sum package-lock.json | cut -d ' ' -f1 > node_modules/.eventeveryday-lock-hash
COPY . .

FROM base AS development
EXPOSE 3000

FROM base AS build
ARG NEXT_PUBLIC_API_URL
ARG INTERNAL_API_URL=http://backend:8000/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    INTERNAL_API_URL=${INTERNAL_API_URL}
RUN npm run build

FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
