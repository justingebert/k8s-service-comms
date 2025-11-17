FROM node:20-slim
LABEL authors="justingebert"

WORKDIR /app
COPY src/common/ src/common/
COPY src/net/sender.js src/net/sender.js
CMD ["node", "src/net/sender.js"]