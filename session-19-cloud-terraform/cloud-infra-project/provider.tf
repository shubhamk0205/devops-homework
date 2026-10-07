# Provider pointed at LocalStack (fake AWS in Docker on localhost:4566).
# For real AWS: delete access_key, secret_key, the skip_* lines,
# s3_use_path_style and the endpoints block, then use real credentials.
provider "aws" {
  region     = var.aws_region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566"
  }

  default_tags {
    tags = {
      Project   = var.project_name
      Session   = "19"
      ManagedBy = "Terraform"
    }
  }
}
