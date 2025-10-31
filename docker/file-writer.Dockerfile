FROM node:20-slim
LABEL authors="justingebert"

WORKDIR /app
COPY src/file/writer.js src/file/writer.js
CMD ["node", "src/file/writer.js"]