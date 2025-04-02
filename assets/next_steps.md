# Next Steps

As mentioned in the main README, this deliverable is meant to be a "minimum lovable product" (MVP) - it's ready for beta testers, but certain additional features are needed to scale and maintain the system long-term. Here are a few suggestions roughly sorted by importance:

## Integrate Emory's preferred authentication tool

The application is secured using API Gateway's built-in API keys because Emory's AWS environment is configured to outright block Cognito, and involving a 3rd party authentication tool like DUO was out of scope. API keys are not meant for end users and we highly recommend integrating a mature authentication tool before rolling out the tool out more broadly.

## Allow users to create jobs themselves

Creating a "job" is currently a manual, technical process because end-users don't work with S3 URIs and translating work IDs to S3 URIs would have involved APIs beyond the project's scope. We created client scripts to simplify the manual process near-term, but long-term we recommend exposing the job creation process directly to users. In practice that would mean formally connecting the application to the core S3 bucket where media is stored, updating the ECS task to translate work IDs to S3 URIs, and adding a page to the frontend where jobs can be created.

## Formalize task recovery process

It should happen less and less as edge cases are found, but at some point a task may crash and leave a work as "IN PROGRESS". You also may find a work with status "FAILED" that you're now ready to re-try. We have a client script for returning those works to "IN QUEUE", but ideally this would be handled automatically or through the frontend.

## Formalize job exploration process

For the MVP we are trusting users to track job names themselves. A nice-to-have feature would be an option to browse from a list of all jobs. The complication this would create, however, is around access management - you may not want all users to be able to see or edit all jobs.

## Add process metadata to items in DynamoDB

Saving the timestamp when each item was created and/or modified, along with the name of the model used to generate the metadata/bias analysis, would be helpful and pretty simple feature to add.

## Set lifecycle policy in S3, Time To Live for DynamoDB

Storage costs for this application should be relatively small, but it could be worth considering a lifecycle policy for uploaded files so that they don't sit around indefinitely once the information has been reviewed, downloaded, and added to some other internal data store. The same goes for DynamoDB - if certain items haven't been touched in 365 days, for example, DynamoDB's TTL feature could be used to automatically remove them to eliminate clutter.

## Use a content delivery network

Our original hope was to serve the ReactJS frontend from S3 using a content delivery network like Amazon Cloudfront, but Emory's AWS environment was configured to block that service so we exposed it through the API Gateway as a workaround. A CDN like Cloudfront would cache content closer to users to reduce both latency and costs. It would also provide added security measures like DDoS protection.

## Consider concurrent ECS tasks

The application is currently configured to run only one ECS task at a time. If the pace of processing works is a concern, you could update the application to increase the number of concurrent tasks.

## Bedrock Batch Processing

This application would be an excellent candidate for Bedrock batch processing. It's cheaper and avoids any potential throttling issues that the realtime API may face.

## Other considerations for maintaining the application long-term

### Costs

This application is serverless, meaning costs are based on how much you use it - if it was deployed and remained untouched for a year, the only costs incurred would be for storing the images and jobs that had already been processed (and that would be very small).

### Upkeep

Because the application is serverless, upkeep is also minimal. The main limitations, as mentioned in next steps, are job creation and recovery. The application doesn't translate Work IDs to S3 URIs today, so creating jobs requires a technical person. Additionally, retrying failed works or works stuck "in progress" is currently handled with a manual script. Once those two details are addressed, the application should require very little attention from engineers.

### Updating prompts

The core application prompts are designed to produce structured outputs, and downstream operations will validate that structure and throw an error if it isn't as expected. That being said, the prompts are written in plain English, so feel free to test out new instructions.
