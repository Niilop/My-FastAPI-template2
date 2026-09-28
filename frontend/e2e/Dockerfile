FROM node:26-bookworm-slim
WORKDIR /app
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci && npx playwright install --with-deps chromium
COPY frontend/playwright.smoke.config.ts ./
COPY frontend/e2e ./e2e
CMD ["npm", "run", "test:smoke"]
