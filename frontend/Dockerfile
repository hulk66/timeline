FROM node:14.15 as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY ./ .
RUN npm run build
# RUN npm audit fix

FROM nginx as production-stage
RUN mkdir /app
COPY --from=build-stage /app/dist /app
COPY docker/nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker/nginx.htpasswd /etc/nginx/conf.d
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]