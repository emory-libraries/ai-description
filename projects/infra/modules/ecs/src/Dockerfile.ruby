# Base image
FROM ruby:3.2-slim

# Set the working directory inside the container
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential imagemagick

# Copy lib directory containing source code and Gemfile
COPY lib/ruby/ ./lib/

# Install Ruby dependencies including AWS SDK gems and retry gem
WORKDIR /app/lib
RUN bundle config set --local without 'development test' && \
    bundle install && \
    gem install aws-sdk-secretsmanager retry_block

# Return to app directory
WORKDIR /app

# Copy the processing script into the container
COPY projects/infra/modules/ecs/src/main.rb .

# Set up Ruby load path to include our library
ENV RUBYLIB=/app/lib/src

# Run the processing script when the container starts
CMD ["ruby", "main.rb"]
