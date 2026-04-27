FROM composer:2.7 AS composer

WORKDIR /app
COPY composer.json /app/composer.json
RUN composer install --no-dev --no-interaction --no-progress --prefer-dist


FROM php:8.3-fpm-alpine

RUN apk add --no-cache \
      bash curl icu-dev libzip-dev oniguruma-dev \
    && docker-php-ext-install pdo_mysql intl zip opcache

WORKDIR /app
COPY --from=composer /app /app

COPY healthcheck.sh /usr/local/bin/healthcheck.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/healthcheck.sh /usr/local/bin/entrypoint.sh

USER www-data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["php-fpm", "-F"]
