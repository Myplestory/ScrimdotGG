#!/bin/bash
# AWS Deployment Script for ScrimGG Django Application
# This script builds and pushes Docker image to ECR and updates ECS services

set -e

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="207108490770"
ECR_REPOSITORY="scrimgg-django"
IMAGE_TAG="${1:-latest}"
CLUSTER_NAME="scrimgg-cluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS deployment...${NC}"

# Step 1: Authenticate Docker with ECR
echo -e "${YELLOW}Step 1: Authenticating Docker with ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
cd "$(dirname "$0")"  # Change to server directory
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Step 3: Push to ECR
echo -e "${YELLOW}Step 3: Pushing image to ECR...${NC}"
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

echo -e "${GREEN}✓ Image pushed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update ECS task definitions to use the new image"
echo "2. Force new deployment: aws ecs update-service --cluster $CLUSTER_NAME --service <service-name> --force-new-deployment"


