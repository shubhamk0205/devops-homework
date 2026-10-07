# Session 18 - Terraform & Infrastructure as Code

In this session I learned what Infrastructure as Code is, how Terraform works (providers, resources,
variables, outputs, state) and the basic AWS services.

| Task | Folder | What I did |
|---|---|---|
| Task 1 - Terraform S3 Demo | [terraform-s3-demo/](terraform-s3-demo/README.md) | Created an S3 bucket with Terraform and ran init, fmt, validate, plan, apply, show, output, destroy |
| Task 2 - AWS Services Research | [aws-services/](aws-services/) | Notes on IAM, EC2, S3, VPC, DynamoDB & RDS |

### Task 2 notes
- [01 - IAM (Governance)](aws-services/01-iam/README.md)
- [02 - EC2 (Compute)](aws-services/02-ec2/README.md)
- [03 - S3 (Storage)](aws-services/03-s3/README.md)
- [04 - VPC (Networking)](aws-services/04-vpc/README.md)
- [05 - DynamoDB & RDS (Databases)](aws-services/05-dynamodb-rds/README.md)

## Setup note - LocalStack
I don't have an AWS account, so for the Terraform part I used **LocalStack 4.4** running in Docker.
It emulates AWS APIs on `http://localhost:4566`. The Terraform AWS provider is pointed to it with an
`endpoints {}` block and dummy `test` credentials. For real AWS the endpoints block and dummy keys are
removed and real credentials are used - the rest of the code is the same.

```text
terraform (hashicorp/aws provider) ──HTTP──> localhost:4566 ──> LocalStack container (fake AWS)
aws cli --endpoint-url=http://localhost:4566 ─────────────────┘   (used to verify resources)
```

Tools: Terraform v1.16.4, hashicorp/aws provider v6.67.0, AWS CLI, Docker.
