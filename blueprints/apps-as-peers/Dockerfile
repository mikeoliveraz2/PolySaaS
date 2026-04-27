FROM node:20-alpine

WORKDIR /app

RUN addgroup -g 10001 app && adduser -D -u 10001 -G app app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . ./

USER app

EXPOSE 3000
CMD ["npm", "run", "start"]
