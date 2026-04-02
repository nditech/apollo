# Apollo Infrastructure

This directory contains the Terraform configuration for Apollo's AWS deployment.

Apollo is expected to run as a Flask/Gunicorn web service plus a separate Celery worker, backed by PostgreSQL/PostGIS, Redis, and S3 attachments.

The infrastructure now includes an end-to-end AWS deployment path for bringing that runtime up in ECS behind an ALB with Route 53 and ACM.

## Structure

- `infra/bootstrap/` creates and manages the S3 bucket used for Terraform remote state.
- `infra/terraform/` contains the main Terraform stack for Apollo infrastructure.
- `infra/scripts/` contains helper scripts for repeatable infrastructure and deployment tasks.

Within `infra/terraform/`, Terraform files are split by concern:

- network and routing
- security groups
- storage
- database
- redis
- ecr
- iam
- secrets
- ecs
- dns / load balancing

Variables and outputs are split into two categories:

- **foundation**: reusable infrastructure-shape inputs and outputs that would likely exist in most Apollo deployments
- **deployment**: inputs and outputs specific to this particular deployment instance

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

The intended long-term network tiering is:

- **public subnets** for the load balancer
- **private app subnets** for ECS tasks
- **private data subnets** for RDS and Redis

For bring-up, ECS tasks are currently running in the public subnets with public IPs enabled. This is a pragmatic temporary choice so tasks can reach required AWS services without first adding NAT gateways or VPC endpoints.

### Security model

Security groups are defined for:

- ALB
- web tasks
- worker tasks
- RDS PostgreSQL
- Redis

The intended traffic flow is:

- internet -> ALB on `443`
- ALB -> web tasks on the application port
- web and worker tasks -> PostgreSQL on `5432`
- web and worker tasks -> Redis on `6379`

The worker service is not intended to receive direct inbound traffic.

Even with ECS tasks currently placed in public subnets for bring-up, security groups still limit inbound access so the web service is reached through the ALB and the worker does not receive direct inbound traffic.

### Database

- PostgreSQL runs on Amazon RDS.
- The DB instance is in the private data subnets.
- The DB is not publicly accessible.
- The current configuration is tuned for development / early infrastructure bring-up rather than hardened production.
- Apollo requires PostGIS support.
- The one-off ECS migration task has successfully run against the AWS database.

### Redis

- Redis runs on Amazon ElastiCache.
- Redis is in the private data subnets.
- Redis is intended for Apollo's Celery/background-task queueing.

### Application runtime

The current Terraform stack includes the first full ECS runtime layer for Apollo:

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

The migration task has successfully completed in ECS, and the web application is reachable at the public hostname.

### S3 attachment authentication

Apollo currently expects explicit AWS credential environment variables during S3 attachment initialization. In this deployment, that means:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

These are stored in Secrets Manager and injected into the ECS task definitions.

This is a bring-up-era compatibility choice driven by the current Apollo codebase. Longer term, it would be preferable to remove this requirement and rely on ECS task-role credentials instead.

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
- ECS tasks currently running in public subnets with public IPs for bring-up
- Apollo currently requiring explicit AWS access keys for S3 attachment initialization
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
- attachments bucket name
- owner tag value

If this stack is reused for another Apollo deployment, these values are among the first things that should be reviewed and changed.

## Working with Terraform

### Bootstrap stack

Use `infra/bootstrap/` only for infrastructure that supports Terraform itself, primarily the remote state bucket.

Typical workflow:

```
cd infra/bootstrap
terraform init
terraform plan
terraform apply
```

### Main Apollo stack

Use `infra/terraform/` for the actual Apollo infrastructure.

Typical workflow:

```
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### Formatting and validation

A useful basic check after reorganizing Terraform files is:

```
terraform fmt
terraform validate
terraform plan
```

`terraform fmt` only reformats files to Terraform's standard style. It does not change infrastructure.

### Build and push helper

Helper scripts for repetitive deployment tasks live under `infra/scripts/`.

Because local development may happen on Apple Silicon hardware while ECS is running `x86_64` workloads, images intended for ECS should be built for `linux/amd64`.

## Notes on state

- Terraform state for the main stack is stored remotely in S3.
- The local machine is no longer the source of truth for Terraform state.
- `.terraform.lock.hcl` should be committed.
- local `*.tfstate` files should not be committed.
- `terraform.tfvars` may contain sensitive deployment values and should not be committed.

## Current validation status

The following milestones have already been validated in AWS:

- Terraform refactoring and file splitting completed with no infrastructure changes in `terraform plan`
- ECS migration task completed successfully
- web application loads at the public hostname
- login works
- default admin password was changed
- a new admin user was created and successfully used to log in

This does not yet mean every application path has been fully validated, but it does confirm that the deployment is beyond initial infrastructure bring-up and into application-level stabilization.

## Near-term expected work

The current stack now includes a working ECS runtime path, but Apollo is not yet fully proven in this environment.

Likely next work includes:

- verifying that the worker service starts cleanly and remains healthy
- testing uploads / attachments end to end against S3
- testing additional core Apollo workflows beyond login and basic admin operations
- deciding whether ECS tasks should remain in public subnets for bring-up or move back to private app subnets with NAT or VPC endpoints
- reducing reliance on explicit AWS access keys for S3 startup if the codebase can be adjusted
- tightening secret handling and other dev-stage compromises before treating the deployment as production-ready

## Intent of the split between `bootstrap` and `terraform`

This split is deliberate.

- `bootstrap` manages the infrastructure Terraform needs in order to operate safely.
- `terraform` manages Apollo itself.

The main Apollo stack should not try to own the backend bucket that stores its own state.
