#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "requests>=2.32"
# ]
# ///

import argparse, csv, json, os, requests
from pathlib import Path

# SERVICE_URL is the url where the AI service is running. It is the endpoint used to create jobs.
SERVICE_URL = os.getenv('SERVICE_URL', 'https://example.com')
# API_KEY is the authentication token necessary to use the service. This will error is it is not set.
API_KEY= os.getenv('API_KEY', None)
# REPO_BUCKET is the URI for the bucket (and folder) containing images already ingested into our repository.
REPO_BUCKET = os.getenv('REPO_BUCKET', 's3://REPO/')
# INGEST_BUCKET is the base URI for the bucket containing images not yet ingested into our repository.
# The images in this bucket are expected to live in folders with the same name as the job being enqueued.
INGEST_BUCKET = os.getenv('INGEST_BUCKET', 's3://INGEST/')

parser = argparse.ArgumentParser(description='Creates bias and metadata jobs for AI processing')
parser.add_argument('--name', '-n', help='Job Name. If this is not supplied, the CSV filename will be used.')
parser.add_argument('type', choices=['bias', 'metadata'], help='Job Type')
parser.add_argument('csv', type=Path, help='Ingest CSV file')
parser.add_argument('--context', '-c', help='Context URI')
parser.add_argument('--metadata', '-m', help='Metadata URI')
parser.add_argument('--dryrun', '-d', action='store_true', help='Print the job metadata, but do not create the job.')
args = parser.parse_args()

if API_KEY is None:
    print("Please set an environment variable for the API_KEY.")
    exit(10)

if args.name is None:
    # The name is optional for this utility, but required for creating jobs. Use the CSV filename if no name is supplied.
    args.name = args.csv.stem

works = {}

with args.csv.open() as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        image_uri = ''
        if row['file_set_id']:
            # If there's a fileset ID, the work has been ingested, so the image is in the repository bucket.
            image_uri = "{}{}".format(REPO_BUCKET, row['page_sha1'])
        else:
            # No fileset, so the image is in the ingest bucket.
            image_uri = "{}{}".format(INGEST_BUCKET, row['page_sha1'])

        if row['work_id'] in works:
            # Work ID already in works
            works[row['work_id']]['image_s3_uris'].append(image_uri)
        else:
            # First time setup for a new work id
            work = {'work_id': row['work_id'], 'image_s3_uris': [image_uri]}
            if args.context is not None:
                work['context_s3_uri'] = args.context
            if args.metadata is not None:
                work['original_metadata_s3_uri'] = args.metadata
            works[row['work_id']] = work

job_data = {'job_name': args.name, 'job_type': args.type, 'works': list(works.values())}

if not args.dryrun:
    response = requests.post(SERVICE_URL, headers={'X-Api-Key': API_KEY}, json=job_data, timeout=30)
    response.raise_for_status()
    print(response.text)
else:
    print(json.dumps(job_data, indent=2))
