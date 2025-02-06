FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy source code and dependencies
COPY src/ ./src/
COPY pyproject.toml README.md ./

# Install the package and dependencies
RUN pip install --no-cache-dir .

# Copy the Lambda handler
COPY infra/modules/lambda/src/functions/predict/index.py .

# Set the CMD to your handler
CMD [ "index.handler" ]
