FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install --omit=dev

COPY server.js .
COPY src ./src

EXPOSE 3000

CMD ["node", "server.js"]
