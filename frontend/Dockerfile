FROM node:16.16.0
WORKDIR /app
COPY . .
RUN npm ci --dev && ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url='./'
