# Architecture

![Architecture](./images/architecture.png)

## Overview

The Archival Image Captioning Assistant follows a serverless architecture pattern centered around an API Gateway. This page describes how the services fit together. To understand the solution from a user perspective, see [workflow.md](./workflow.md)

### Amazon API Gateway

Whether communicating via command line or web browser, interactions with the application are secured using API Gateway's API keys. Requests prepended with `/api/` will attempt to route to one of the Lambda functions, while the rest are treated as webpage paths.

### Amazon S3

- The static ReactJS frontend is served from a private S3 bucket

- An "uploads" S3 bucket hosts copies of the media files the application is meant to process, like JPEGs, user-provided historical context, and existing metadata. Part of the motivation for this was to avoid directly interacting with the core S3 bucket where Emory Libraries manages their original media.

### AWS Lambda

Lambdas are used to carry out most of the application logic.

- `create-job` accepts a job definition, which includes job name, task type (metadata or bias analysis), and a list of work details (image URIs, existing metadata, historical contexts). It creates an SQS message for each work in the job and, if there is no ECS Fargate task running, it kicks off an ECS Fargate processing task.

- `job-progress` accepts a `job_name`, queries DynamoDB, and returns the status of each work in the job

- `get-results` retrieves the results of each work in a job from DynamoDB

- `get-presigned-url` accepts an S3 URI and generates a pre-signed URL for that file so that the frontend client can retrieve the image and display it.

- `update-results` allows users to submit corrections to LLM generations, which are persisted in DynamoDB.

### ECS Fargate

ECS Fargate Tasks are used to asynchronously process all works in SQS. These tasks are where the main library is leveraged and where Bedrock is invoked. The task itself is job agnostic - if the queue has 10 metadata works from Job A, then 5 bias works from Job B, then 2 more works from Job A, it'll handle each work one at a time in the order they were queued. Once SQS is empty, it'll shut down to avoid incurring additional costs. Currently the solution is designed to only ever use a single Fargate task to handle all SQS messages, but this could be increased as needed.

### DynamoDB

DynamoDB is where all generated bias and metadata information are stored. Each row represents a work - the partition key is job_name and sort key is work_id. Here is a list of all the fields in the table as of 2025-03-19:

- job_name
- work_id
- actions
- context_s3_uri
- contextual_info
- date
- description
- format
- genre
- image_s3_uris
- job_type
- location
- metadata_biases
- objects
- original_metadata_s3_uri
- page_biases
- people
- publication_info	
- topics	
- transcription	
- work_status

### Amazon CloudWatch

ECS and Lambda logs can be found in CloudWatch.

## Limitations

This architecture was constrained by what services were allowed in our sandbox environment.

- Ideally, the frontend would be served behind Cloudfront, but the service is not permitted in Emory's AWS environment. Instead, we're serving it directly using the API Gateway and grouping the backend endpoints within the `/api/` path.
- Ideally the application would be secured with a user and access management solution like Cognito, but Cognito is not permitted in Emory's AWS environment. Involving Emory's interal tool was out-of-scope, so we secured the entire application using API Gateway's built in API Keys feature. This was not meant to be a long-term solution and we highly recommend integrating your preferred user and access management tool as soon as possible.
