#!/usr/bin/env bash
#
# Build Apollo's production Docker image for ECS/Fargate on AWS.
#
# Important:
# - Forces linux/amd64 so builds from Apple Silicon Macs still run on ECS.
# - Builds the production target from the multi-stage Dockerfile.
# - Tags both the local image and the ECR image.
#
# Usage:
#   ./scripts/build-ecr.sh 2026-03-31.2
#
# Optional env vars:
#   AWS_REGION=us-east-1
#   AWS_ACCOUNT_ID=592016371171
#   ECR_REPOSITORY=apollo

set -euo pipefail

TAG="${1:-}"

if [[ -z "$TAG" ]]; then
  echo "Usage: $0 <image-tag>"
  exit 1
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-592016371171}"
ECR_REPOSITORY="${ECR_REPOSITORY:-apollo}"

LOCAL_IMAGE="${ECR_REPOSITORY}:${TAG}"
ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${TAG}"

echo "Building ${LOCAL_IMAGE} for linux/amd64..."
docker buildx build \
  --platform linux/amd64 \
  --target production \
  -t "${LOCAL_IMAGE}" \
  .

echo "Logging into ECR..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Tagging image as ${ECR_IMAGE}..."
docker tag "${LOCAL_IMAGE}" "${ECR_IMAGE}"

echo "Pushing ${ECR_IMAGE}..."
docker push "${ECR_IMAGE}"

echo
echo "Done."
echo "Image URI:"
echo "${ECR_IMAGE}"