# Apollo Infrastructure

This directory contains the Terraform configuration for Apollo's AWS deployment.

Apollo is expected to run as a Flask/Gunicorn web service plus a separate Celery worker, backed by PostgreSQL/PostGIS, Redis, and S3 attachments.

The infrastructure now also includes the first ECS/ALB/Route 53 deployment path for bringing that runtime up in AWS.

## Structure

- `infra/bootstrap/` creates and manages the S3 bucket used for Terraform remote state.
- `infra/terraform/` contains the main Terraform stack for Apollo infrastructure.
- `infra/scripts/` contains helper scripts for repeatable infrastructure/deployment tasks such as building and pushing ECS-compatible container images.

## Current architecture

The current AWS layout is intentionally modest: cheap where possible, but stable enough not to be a constant operational headache.

### State and storage

- Terraform remote state is stored in an S3 bucket managed by the bootstrap stack.
- Apollo attachments are stored in a separate S3 bucket.
- Both buckets have public access blocked.
- The attachments bucket has default encryption and versioning enabled.

### Networking

The main Terraform stack currently creates:

- one VPC
- two public subnets
- two private app subnets
- two private data subnets
- one internet gateway
- one public route table associated to the public subnets

The intended network tiering is:

- **public subnets** for the load balancer
- **private app subnets** for ECS tasks
- **private data subnets** for RDS and Redis

### Security model

Security groups are defined for the future runtime layout:

- ALB
- web tasks
- worker tasks
- RDS PostgreSQL
- Redis

The intended traffic flow, once the runtime layer is in place, is:

- internet -> ALB on `443`
- ALB -> web tasks on the application port
- web and worker tasks -> PostgreSQL on `5432`
- web and worker tasks -> Redis on `6379`

The worker service is not intended to receive direct inbound traffic.

### Database

- PostgreSQL runs on Amazon RDS.
- The DB instance is in the private data subnets.
- The DB is not publicly accessible.
- The current configuration is tuned for development / early infrastructure bring-up rather than hardened production.
- Migrations should ensure the PostGIS extension is enabled as Apollo requires.

### Redis

- Redis runs on Amazon ElastiCache.
- Redis is in the private data subnets.
- Redis is intended for Apollo's Celery/background-task queueing.

### Application runtime

The current Terraform stack now includes the first ECS runtime layer for Apollo:

- ECS cluster
- task execution role and task role
- Secrets Manager secrets for application runtime
- CloudWatch log groups
- ECS task definitions for migration, web, and worker
- ALB and listeners
- ECS services for web and worker
- Route 53 alias for the public hostname

Apollo currently uses one Docker image with different commands for three roles:

- **migration**: `flask db upgrade`
- **web**: `gunicorn -c gunicorn.py apollo.runner`
- **worker**: `celery --app=apollo.runner worker --beat --loglevel=WARNING --concurrency=2 --without-gossip --without-mingle --optimization=fair`

## Design priorities

This infrastructure is being built with the following priority order:

1. stable enough not to require constant babysitting
2. as inexpensive as practical
3. only then, additional elegance or scale

In practice, that currently means:

- preferring managed services when they materially reduce operational pain
- avoiding premature high-availability spend where it is not yet justified
- keeping the network and security layout sane from the start
- using S3 instead of EFS for attachments

A useful shorthand for the approach is **low pain per dollar**.

## Current dev-stage compromises

Some current settings are appropriate for early-stage or development use, but should be revisited before treating this as real production infrastructure.

Examples include:

- RDS `skip_final_snapshot = true`
- RDS `deletion_protection = false`
- single-AZ database deployment
- secrets currently simple enough for bootstrapping rather than a final production secret-management pattern

## Deployment-specific configuration choices

Some parts of this stack are reusable AWS/Apollo infrastructure patterns. Others are specific choices for this deployment and should be treated as configuration inputs rather than baked-in assumptions.

Examples of deployment-specific choices currently include:

- public hostname: `witness.cocitizen.com`
- default sender email: `witness@cocitizen.com`
- timezone: `America/New_York`
- ACM certificate for the public hostname
- Docker image tag/version used for ECS task definitions
- health check path used by the ALB
- runtime secrets such as the Flask `SECRET_KEY` and database password

If this stack is reused for another Apollo deployment, these values are among the first things that should be reviewed and changed.


## Working with Terraform

### Bootstrap stack

Use `infra/bootstrap/` only for infrastructure that supports Terraform itself, primarily the remote state bucket.

Typical workflow:

```bash
cd infra/bootstrap
terraform init
terraform plan
terraform apply
```

### Main Apollo stack

Use `infra/terraform/` for the actual Apollo infrastructure.

Typical workflow:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### Build and push helper

A helper script for building and pushing ECS-compatible container images lives under `infra/scripts/`.

Because local development may happen on Apple Silicon hardware while ECS is running x86_64 workloads, images intended for ECS should be built for `linux/amd64`.

## Notes on state

- Terraform state for the main stack is stored remotely in S3.
- The local machine is no longer the source of truth for Terraform state.
- `.terraform.lock.hcl` should be committed.
- local `*.tfstate` files should not be committed.

## Near-term expected work

The current stack now includes the first ECS runtime layer, but Apollo is not yet fully proven in this environment.

Likely next work includes:

- running the one-off migration task successfully in ECS
- confirming that Apollo migrations enable PostGIS cleanly in AWS
- verifying that the web service comes healthy behind the ALB
- verifying that the worker service starts and remains healthy
- deciding whether ECS tasks should remain in public subnets for bring-up or move back to private app subnets with NAT or VPC endpoints
- tightening secret handling and other dev-stage compromises before treating the deployment as production-ready

## Intent of the split between `bootstrap` and `terraform`

This split is deliberate.

- `bootstrap` manages the infrastructure Terraform needs in order to operate safely.
- `terraform` manages Apollo itself.

The main Apollo stack should not try to own the backend bucket that stores its own state.
