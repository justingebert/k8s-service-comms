FROM node:20-alpine

ENV NODE_ENV=production \
    PORT=8080 \
    BACKEND_URL=http://backend:8080

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY . ./

EXPOSE 8080
CMD ["node", "server.js"]
