# Task 1 - Terraform S3 Demo

In this task I created an S3 bucket with Terraform and went through the full Terraform workflow:
`init -> fmt -> validate -> plan -> apply -> show -> output -> destroy`.

---

## Note: I used LocalStack instead of real AWS

I don't have an AWS account, so I used **LocalStack**. LocalStack is a tool that runs in a Docker
container and pretends to be AWS on `http://localhost:4566`. Terraform talks to it exactly like it talks
to real AWS (same `hashicorp/aws` provider, same resource blocks), only the endpoint URL is different.

I started it like this:

```bash
docker run -d --name localstack -p 4566:4566 localstack/localstack:4.4
```

> The `latest` image (2026.9.1) did not start for me. It exited with
> `License activation failed! ... Please set the LOCALSTACK_AUTH_TOKEN variable`.
> So I used the older tag **`localstack/localstack:4.4`** (LocalStack 4.4.0), which runs without a token.

```text
LocalStack version: 4.4.0
LocalStack build date: 2025-05-08
LocalStack build git hash: 21f6e5fb2

Ready.
```

**For real AWS:** in `provider.tf` I would remove `access_key`, `secret_key`, the three `skip_*` lines,
`s3_use_path_style` and the `endpoints { }` block, and then run `aws configure` with real credentials.
Everything else (main.tf, variables, outputs) stays the same.

---

## Project Structure

```text
terraform-s3-demo/
├── main.tf             # the S3 bucket resource
├── variables.tf        # input variables (region, bucket name, environment)
├── outputs.tf          # values printed after apply
├── provider.tf         # terraform block + AWS provider (pointed at LocalStack)
├── terraform.tfvars    # actual values for the variables
├── .terraform.lock.hcl # provider version lock (created by init)
└── README.md
```

`.terraform/` and `terraform.tfstate` are in `.gitignore` - they are local files and state can contain sensitive data.
`terraform.tfvars` is committed because it only has a bucket name and region, nothing secret.

## How the files connect

```text
terraform.tfvars ──> variables.tf ──> provider.tf (region)
                                  └─> main.tf (aws_s3_bucket.demo)
                                            │
                                            v
                                       outputs.tf (name, arn, region)
```

---

## The Code

### provider.tf
```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566"
  }
}
```
- `access_key` / `secret_key = "test"` - LocalStack accepts any dummy keys.
- `skip_*` - stops the provider from checking the keys with real AWS STS / EC2 metadata.
- `s3_use_path_style` - uses `localhost:4566/bucket` instead of `bucket.localhost:4566` (needed for LocalStack).

### variables.tf
```hcl
variable "aws_region" {
  description = "AWS region where the S3 bucket will be created."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket (must be globally unique on real AWS)."
  type        = string
}

variable "environment" {
  description = "Environment name used in tags."
  type        = string
  default     = "dev"
}
```

### terraform.tfvars
```hcl
aws_region  = "us-east-1"
bucket_name = "shubham-session18-s3-demo"
environment = "dev"
```

### main.tf
```hcl
resource "aws_s3_bucket" "demo" {
  bucket        = var.bucket_name
  force_destroy = true

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "Session18"
  }
}
```
`force_destroy = true` lets `terraform destroy` delete the bucket even if it has objects inside.

### outputs.tf
```hcl
output "bucket_name" {
  description = "Name of the S3 bucket."
  value       = aws_s3_bucket.demo.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket."
  value       = aws_s3_bucket.demo.arn
}

output "bucket_region" {
  description = "AWS region of the S3 bucket."
  value       = aws_s3_bucket.demo.region
}
```

---

## Workflow

```text
init ──> fmt ──> validate ──> plan ──> apply ──> show / output ──> destroy
```

### Step 1 - terraform init
Downloads the AWS provider plugin and creates the lock file.

```bash
terraform init
```
```text
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 6.0"...
- Installing hashicorp/aws v6.67.0...
- Installed hashicorp/aws v6.67.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
...
Terraform has been successfully initialized!
```
What I observed: a `.terraform/` folder with the provider binary and a `.terraform.lock.hcl` file were created.

### Step 2 - terraform fmt
Formats all `.tf` files to the standard style.

```bash
terraform fmt
echo $?
```
```text
0
```
What I observed: no output. `fmt` only prints the names of files it changed, and my files were already formatted, so nothing was printed.

### Step 3 - terraform validate
Checks the syntax and that references are correct (no AWS calls).

```bash
terraform validate
```
```text
Success! The configuration is valid.
```

### Step 4 - terraform plan
Shows what Terraform is going to do. I saved the plan to a file so apply runs exactly this plan.

```bash
terraform plan -out=tfplan
```
```text
Terraform will perform the following actions:

  # aws_s3_bucket.demo will be created
  + resource "aws_s3_bucket" "demo" {
      + arn                         = (known after apply)
      + bucket                      = "shubham-session18-s3-demo"
      + force_destroy               = true
      + id                          = (known after apply)
      + region                      = "us-east-1"
      + tags                        = {
          + "Environment" = "dev"
          + "ManagedBy"   = "Terraform"
          + "Name"        = "shubham-session18-s3-demo"
          + "Project"     = "Session18"
        }
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + bucket_arn    = (known after apply)
  + bucket_name   = "shubham-session18-s3-demo"
  + bucket_region = "us-east-1"

Saved the plan to: tfplan
```
What I observed: `+` means create. Values like `arn` are `(known after apply)` because AWS gives them only after the bucket exists.

### Step 5 - terraform apply
```bash
terraform apply tfplan
```
```text
aws_s3_bucket.demo: Creating...
aws_s3_bucket.demo: Creation complete after 1s [id=shubham-session18-s3-demo]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

bucket_arn = "arn:aws:s3:::shubham-session18-s3-demo"
bucket_name = "shubham-session18-s3-demo"
bucket_region = "us-east-1"
```
What I observed: because I applied a saved plan, it did not ask "yes" again. A `terraform.tfstate` file was created.

I checked with the AWS CLI that the bucket really exists (dummy creds for LocalStack):

```bash
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 s3api get-bucket-tagging --bucket shubham-session18-s3-demo
```
```text
2026-10-08 00:18:46 shubham-session18-s3-demo
{
    "TagSet": [
        {
            "Key": "Environment",
            "Value": "dev"
        },
        {
            "Key": "Project",
            "Value": "Session18"
        },
        {
            "Key": "ManagedBy",
            "Value": "Terraform"
        },
        {
            "Key": "Name",
            "Value": "shubham-session18-s3-demo"
        }
    ]
}
```

### Step 6 - terraform show
Shows what is stored in the state file in a readable way.

```bash
terraform show
```
```text
# aws_s3_bucket.demo:
resource "aws_s3_bucket" "demo" {
    arn                         = "arn:aws:s3:::shubham-session18-s3-demo"
    bucket                      = "shubham-session18-s3-demo"
    bucket_domain_name          = "shubham-session18-s3-demo.s3.amazonaws.com"
    bucket_region               = "us-east-1"
    force_destroy               = true
    id                          = "shubham-session18-s3-demo"
    region                      = "us-east-1"
    request_payer               = "BucketOwner"
    tags                        = {
        "Environment" = "dev"
        "ManagedBy"   = "Terraform"
        "Name"        = "shubham-session18-s3-demo"
        "Project"     = "Session18"
    }
    ...
    server_side_encryption_configuration {
        rule {
            bucket_key_enabled = false

            apply_server_side_encryption_by_default {
                kms_master_key_id = null
                sse_algorithm     = "AES256"
            }
        }
    }

    versioning {
        enabled    = false
        mfa_delete = false
    }
}

Outputs:

bucket_arn = "arn:aws:s3:::shubham-session18-s3-demo"
bucket_name = "shubham-session18-s3-demo"
bucket_region = "us-east-1"
```
What I observed: the bucket got default AES256 encryption even though I did not ask for it (same as real S3 does now).

### Step 7 - terraform output
```bash
terraform output
terraform output -raw bucket_arn
```
```text
bucket_arn = "arn:aws:s3:::shubham-session18-s3-demo"
bucket_name = "shubham-session18-s3-demo"
bucket_region = "us-east-1"
arn:aws:s3:::shubham-session18-s3-demo
```
What I observed: `-raw` prints only the value without quotes, useful in shell scripts.

### Step 8 - terraform destroy
```bash
terraform destroy -auto-approve
```
```text
aws_s3_bucket.demo: Refreshing state... [id=shubham-session18-s3-demo]

Terraform will perform the following actions:

  # aws_s3_bucket.demo will be destroyed
  - resource "aws_s3_bucket" "demo" {
      - arn                         = "arn:aws:s3:::shubham-session18-s3-demo" -> null
      - bucket                      = "shubham-session18-s3-demo" -> null
      ...
    }

Plan: 0 to add, 0 to change, 1 to destroy.
...
aws_s3_bucket.demo: Destroying... [id=shubham-session18-s3-demo]
aws_s3_bucket.demo: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```
```text
```
What I observed: the list is empty now, the bucket is gone.

---

## What I learned
- Terraform is declarative: I only wrote "I want a bucket with these tags", and Terraform figured out the API calls.
- `plan` is a safe preview, `apply` actually changes things, and the state file is how Terraform remembers what it created.
- Variables + tfvars keep values out of the main code, so I can change the bucket name without touching main.tf.
- The same code can target LocalStack or real AWS just by changing the provider block.
