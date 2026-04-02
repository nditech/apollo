#!/usr/bin/env bash
#
# Show the current ECS tasks for a service and summarize their status.
#
# Usage:
#   ./infra/scripts/ecs-service-tasks.sh apollo-dev apollo-dev-web
#
# Optional env vars:
#   AWS_REGION=us-east-1

set -euo pipefail

CLUSTER="${1:-}"
SERVICE="${2:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

if [[ -z "$CLUSTER" || -z "$SERVICE" ]]; then
  echo "Usage: $0 <cluster-name> <service-name>"
  exit 1
fi

TASK_ARNS=$(aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --region "$AWS_REGION" \
  --query 'taskArns' \
  --output text)

if [[ -z "$TASK_ARNS" ]]; then
  echo "No tasks found for service '$SERVICE' in cluster '$CLUSTER'."
  exit 0
fi

aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks $TASK_ARNS \
  --region "$AWS_REGION" \
  --query 'tasks[*].{
    taskArn: taskArn,
    lastStatus: lastStatus,
    desiredStatus: desiredStatus,
    stopCode: stopCode,
    stoppedReason: stoppedReason,
    containers: containers[*].{
      name: name,
      lastStatus: lastStatus,
      reason: reason,
      exitCode: exitCode
    }
  }'