#!/bin/bash

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to display usage instructions
usage() {
    echo "Usage: $0 [-a ACCOUNT_ID] [-r REGION]"
    echo "  -a    AWS Account ID (optional, defaults to current AWS account)"
    echo "  -r    AWS Region (optional, defaults to current AWS region)"
    exit 1
}

# Function to detect AWS region from various sources
get_aws_region() {
    if [ -n "$AWS_REGION" ]; then
        echo "$AWS_REGION"
        return 0
    fi
    if [ -n "$AWS_DEFAULT_REGION" ]; then
        echo "$AWS_DEFAULT_REGION"
        return 0
    fi
    local config_region=$(aws configure get region)
    if [ -n "$config_region" ]; then
        echo "$config_region"
        return 0
    fi
    if curl -s -m 1 http://169.254.169.254/latest/meta-data/ > /dev/null; then
        local metadata_region=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
        if [ -n "$metadata_region" ]; then
            echo "$metadata_region"
            return 0
        fi
    fi
    echo "us-east-1"
    return 0
}

# Parse command line arguments
while getopts "a:r:h" opt; do
    case $opt in
        a) ACCOUNT_ID="$OPTARG" ;;
        r) REGION="$OPTARG" ;;
        h) usage ;;
        ?) usage ;;
    esac
done

# If ACCOUNT_ID not provided, get it from AWS
if [ -z "$ACCOUNT_ID" ]; then
    echo "${YELLOW}No account ID provided, fetching from AWS...${NC}"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ $? -ne 0 ]; then
        echo "${RED}Failed to get AWS account ID. Are you logged in to AWS CLI?${NC}"
        exit 1
    fi
fi

# If REGION not provided, get it from AWS
if [ -z "$REGION" ]; then
    echo "${YELLOW}No region provided, detecting region...${NC}"
    REGION=$(get_aws_region)
    echo "${GREEN}Using region: ${REGION}${NC}"
fi

# Configuration variables
BUCKET_NAME="${ACCOUNT_ID}-${REGION}-terraform-state"
TABLE_NAME="${ACCOUNT_ID}-${REGION}-terraform-state-locking"
TERRAFORM_DIR="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/projects/infra"
BACKEND_CONFIG_FILE="${TERRAFORM_DIR}/backend.tfvars"

echo "${YELLOW}Creating Terraform backend resources...${NC}"
echo "${YELLOW}Using Account: ${ACCOUNT_ID}${NC}"
echo "${YELLOW}Using Region: ${REGION}${NC}"

# Check if S3 bucket exists
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "${GREEN}Bucket $BUCKET_NAME already exists${NC}"
else
    echo "${YELLOW}Creating S3 bucket for Terraform state...${NC}"
    # Create the S3 bucket using s3 mb
    if ! aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"; then
        echo "${RED}Failed to create S3 bucket${NC}"
        exit 1
    fi

    # Enable versioning on the bucket
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled

    # Enable server-side encryption
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'

    # Block all public access
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

    echo "${GREEN}S3 bucket created and configured${NC}"
fi

# Check if DynamoDB table exists
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" 2>/dev/null; then
    echo "${GREEN}DynamoDB table $TABLE_NAME already exists${NC}"
else
    echo "${YELLOW}Creating DynamoDB table for state locking...${NC}"
    # Create the DynamoDB table
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null

    if [ $? -eq 0 ]; then
        echo "${YELLOW}Waiting for DynamoDB table to be created...${NC}"
        aws dynamodb wait table-exists \
            --table-name "$TABLE_NAME" \
            --region "$REGION"
        echo "${GREEN}DynamoDB table created${NC}"
    else
        echo "${RED}Failed to create DynamoDB table${NC}"
        exit 1
    fi
fi

# Create terraform directory if it doesn't exist
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "${YELLOW}Creating terraform directory...${NC}"
    mkdir -p "$TERRAFORM_DIR"
fi

# Create backend.tfvars file with configuration
echo "${YELLOW}Creating backend configuration file...${NC}"
cat > "$BACKEND_CONFIG_FILE" << EOF
# Terraform backend configuration
# Generated by create-tf-backend.sh on $(date)
#
# bucket:         S3 bucket for storing terraform state
# key:            Path to the state file within the bucket
# region:         AWS region where the bucket exists
# dynamodb_table: DynamoDB table for state locking

bucket         = "${BUCKET_NAME}"
key            = "terraform.tfstate"
region         = "${REGION}"
dynamodb_table = "${TABLE_NAME}"
EOF

if [ $? -eq 0 ]; then
    echo "${GREEN}Backend configuration written to: ${BACKEND_CONFIG_FILE}${NC}"
else
    echo "${RED}Failed to create backend configuration file${NC}"
    exit 1
fi

echo "${GREEN}Backend configuration has been written to: ${BACKEND_CONFIG_FILE}${NC}"
echo "${GREEN}You can now run: terraform init -backend-config=${BACKEND_CONFIG_FILE}${NC}"
