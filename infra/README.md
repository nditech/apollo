# Apollo Infrastructure

This directory contains the Terraform configuration for Apollo's AWS deployment.

Apollo is expected to run as a Flask/Gunicorn web service plus a separate Celery worker, backed by PostgreSQL/PostGIS, Redis, and S3 attachments.

## Structure

- `infra/bootstrap/` creates and manages the S3 bucket used for Terraform remote state.
- `infra/terraform/` contains the main Terraform stack for Apollo infrastructure.

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

## Notes on state

- Terraform state for the main stack is stored remotely in S3.
- The local machine is no longer the source of truth for Terraform state.
- `.terraform.lock.hcl` should be committed.
- local `*.tfstate` files should not be committed.

## Near-term expected additions

The current stack is not yet complete. Likely next pieces include:

- a one-off application migration task during deployment
- ECR repository
- ECS services for web and worker
- ALB
- certificate and DNS wiring
- ECS task definitions and runtime configuration for web, worker, and migration
- confirmation that Apollo migrations enable PostGIS cleanly in the AWS environment

## Intent of the split between `bootstrap` and `terraform`

This split is deliberate.

- `bootstrap` manages the infrastructure Terraform needs in order to operate safely.
- `terraform` manages Apollo itself.

The main Apollo stack should not try to own the backend bucket that stores its own state.
