FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy lib directory containing source code and package config
COPY lib/ ./lib/

# Install package and dependencies from lib directory
RUN pip install --no-cache-dir ./lib/

# Copy the processing script into the container
COPY projects/infra/modules/ecs/src/main.py .

# Run the processing script when the container starts
CMD ["python", "main.py"]