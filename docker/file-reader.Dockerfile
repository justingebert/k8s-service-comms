FROM node:20-slim
LABEL authors="justingebert"

WORKDIR /app
COPY src/common/ src/common/
COPY src/file/reader.js src/file/reader.js
CMD ["node", "src/file/reader.js"]