FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# The lockfile is maintained on Windows and omits Linux-only optional native
# package records. Install only version-matched Alpine artifacts needed by the
# locked build; keep the application dependency graph unchanged.
RUN npm ci \
    && npm install --no-save \
      @oxc-parser/binding-linux-x64-musl@0.120.0 \
      @rolldown/binding-linux-x64-musl@1.2.1 \
      @tailwindcss/oxide-linux-x64-musl@4.3.3 \
      lightningcss-linux-x64-musl@1.33.0 \
    && npm install --prefix /tmp/lightningcss-1.32 --no-save \
      lightningcss-linux-x64-musl@1.32.0 \
    && cp -R /tmp/lightningcss-1.32/node_modules/lightningcss-linux-x64-musl \
      node_modules/@tailwindcss/node/node_modules/

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_USE_MOCK_API=false
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_USE_MOCK_API=${VITE_USE_MOCK_API} \
    VITE_SUPABASE_URL=${VITE_SUPABASE_URL} \
    VITE_SUPABASE_PUBLISHABLE_KEY=${VITE_SUPABASE_PUBLISHABLE_KEY} \
    NITRO_PRESET=node-server

RUN npm run build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

WORKDIR /app

COPY --from=build --chown=node:node /app/.output ./.output

USER node

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
