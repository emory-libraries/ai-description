#!/bin/bash

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Copy/paste this script into your dev instance to set it up

# Exit immediately if a command exits with a non-zero status
set -e

# Update system packages
sudo yum update -y

# Install yum-utils, git, make, and Docker
sudo yum install -y yum-utils git make docker

# Start Docker
sudo systemctl start docker.service

# Set user as owner of Docker
sudo chown $USER:docker /var/run/docker.sock

# Add HashiCorp repository
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo

# Install Terraform
sudo yum install -y terraform

# Prompt for GitHub username and PAT
read -p "Enter your GitHub username: " USERNAME
read -sp "Enter your GitHub Personal Access Token: " PAT
echo  # Move to a new line after the hidden input

# Clone the repository
REPO_URL="https://${USERNAME}:${PAT}@github.com/emory-libraries/ai-description.git"
git clone "${REPO_URL}" ~/ai-description

# Install dependencies for Python 3.12
sudo yum groupinstall "Development Tools" -y
sudo yum install openssl-devel bzip2-devel libffi-devel -y

# Download and unpack Python 3.12
cd ~
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar xzf Python-3.12.0.tgz
cd Python-3.12.0

# Configure and build Python 3.12
./configure --enable-optimizations
make
sudo make altinstall
echo $(python3.12 --version)

# Hop into the repo and create a virtual environment
cd ~/ai-description
python3.12 -m venv venv
source venv/bin/activate

echo "Script completed successfully!"