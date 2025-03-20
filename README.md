# Archival Image Captioning Assistant

This repository contains the full-stack solution for the Archival Image Captioning Assistant.

This is meant to be a "minimum lovable product" (MVP) meaning it's ready for beta testers but may need modifications before being released to wider audiences.

Workflow is outlined in [this markdown file](./assets/workflow.md).

Architecture is outlined [here](./assets/architecture.md).

Next steps and long-term sustainability notes [here](./assets/next_steps.md).

## Code organization

```
lib/				- Python/Ruby libraries defining app logic
notebooks/			- Examples interacting with API
projects/
    frontend/		- ReactJS frontend
    infra/			- Terraform setup
    research/		- Jupyer notebooks from experiments
```

## Deployment prerequisites

- AWS CLI configured with appropriate credentials
- Terraform (>= 1.0.0)
- Make
- Python 3.x
- Docker
- Node.js/npm (for frontend components)

## Getting Started

1. Clone the repository
2. Configure your AWS credentials or use instance roles (usually AWS_PROFILE=default):

```bash
export AWS_PROFILE=your-profile-name
```

3. Update the `dev.tfvars` file with your configuration:

```hcl
vpc_id = ""  # Leave empty to create new VPC
app_name = "ai-description"
deployment_stage = "dev"
deployment_name = "your-deployment-name"  # Required
```

## Available Make Commands

### Setup Commands

- `make createPythonEnvironment` - Creates a Python virtual environment
- `make createTerraformBackend` - Creates Terraform backend configuration in S3 and DynamoDB
- `make installPythonRequirements` - Installs Python dependencies
- `make installJavaScriptRequirements` - Installs JavaScript dependencies
- `make install` - Installs all dependencies

### Terraform Commands

- `make terraformFmtValidate` - Formats and validates Terraform code (automatically applied to other Make rules)
- `make terraformInit` - Initializes Terraform configuration
- `make terraformPlan` - Creates Terraform plan
- `make terraformApply` - Applies Terraform changes
- `make terraformDestroy` - Destroys Terraform infrastructure

### Cleanup Commands

- `make cleanPython` - Cleans Python artifacts
- `make cleanTerraform` - Cleans Terraform artifacts
- `make cleanTypeScript` - Cleans TypeScript artifacts
- `make clean` - Cleans all artifacts

## Deployment Steps

1. Initialize the project:

```bash
make terraformInit
```

2. Create and review the deployment plan:

```bash
make terraformPlan
```

3. Apply the changes:

```bash
make terraformApply
```

4. To destroy the infrastructure:

```bash
make terraformDestroy
```

## Infrastructure Components

The deployment creates the following AWS resources:

- VPC with public/private subnets and VPC endpoints
- API Gateway
- Lambda functions
- DynamoDB tables
- S3 buckets
- ECS cluster
- CloudWatch logs
- IAM roles and policies
- EventBridge rules
- SQS queues
- ECR repositories

## Notes

- All commands require valid AWS credentials
- The `dev.tfvars` file must be properly configured before deployment
- Use `make help` to see all available commands
- Infrastructure changes should be reviewed carefully before applying
