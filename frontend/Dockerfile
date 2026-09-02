FROM node:24-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .

FROM base AS development
EXPOSE 3000

FROM base AS build
RUN npm run build

FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]

