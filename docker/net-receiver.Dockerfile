FROM node:20-slim
LABEL authors="justingebert"

WORKDIR /app
COPY src/common/ src/common/
COPY src/net/receiver.js src/net/receiver.js
CMD ["node", "src/net/receiver.js"]