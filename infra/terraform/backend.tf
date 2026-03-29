terraform {
  backend "s3" {
    bucket       = "cdoten-apollo-terraform-state"
    key          = "apollo/dev/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
