FROM php:8.1-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libzip-dev \
    libxml2-dev \
    libicu-dev \
    libonig-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    unzip \
    git \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Configure PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install \
    pdo_mysql \
    mysqli \
    gd \
    zip \
    xml \
    intl \
    mbstring \
    curl \
    openssl \
    bcmath

# Enable Apache modules
RUN a2enmod rewrite headers

# Download and install SuiteCRM
RUN curl -L https://github.com/salesagility/SuiteCRM/archive/v8.2.4.tar.gz -o suitecrm.tar.gz \
    && tar -xzf suitecrm.tar.gz \
    && mv SuiteCRM-8.2.4 /var/www/html/suitecrm \
    && rm suitecrm.tar.gz

# Set permissions
RUN chown -R www-data:www-data /var/www/html/suitecrm \
    && chmod -R 755 /var/www/html/suitecrm

# Create SuiteCRM config directory
RUN mkdir -p /var/www/html/suitecrm/config \
    && chown -R www-data:www-data /var/www/html/suitecrm/config

# Copy custom configuration
COPY config_override.php /var/www/html/suitecrm/config_override.php

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start Apache
CMD ["apache2-foreground"]