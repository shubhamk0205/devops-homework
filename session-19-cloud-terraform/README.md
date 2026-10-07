# Session 19 - Cloud & Terraform in Action

In this session I used Terraform to build a small end-to-end AWS infrastructure:
VPC -> public subnet (IGW + route table) -> security group -> EC2 instance, plus an S3 bucket.

| Task | Folder | What I did |
|---|---|---|
| End-to-end cloud infrastructure with Terraform | [cloud-infra-project/](cloud-infra-project/README.md) | Providers, variables, resources, outputs, dependencies, state, plan / apply / destroy |

```text
Terraform
├── VPC              10.20.0.0/16
├── Subnet           10.20.1.0/24 (public, via IGW + route table)
├── Security Group   in: 22, 80 / out: all
├── EC2              t3.micro in the public subnet
└── S3               bucket with versioning
```

## Deliverables
| Deliverable | Where |
|---|---|
| Terraform project | [cloud-infra-project/](cloud-infra-project/) (`*.tf`, `terraform.tfvars`) |
| AWS resources | created on LocalStack, verified with the AWS CLI ([README section](cloud-infra-project/README.md#verifying-the-aws-resources)) |
| Architecture diagram | ASCII in the project README + [screenshots/architecture.png](screenshots/architecture.png) |
| Screenshots | [screenshots/](screenshots/) - apply, state/output, AWS CLI checks, terraform graph, destroy |
| Terraform commands | [Command walkthrough](cloud-infra-project/README.md#terraform-commands-what-i-ran) |
| README.md | this file + [cloud-infra-project/README.md](cloud-infra-project/README.md) |

## Setup note - LocalStack
I don't have an AWS account, so I ran **LocalStack 4.4** in Docker (`localstack/localstack:4.4`, the
`latest` image needs an auth token now). LocalStack emulates AWS APIs on `http://localhost:4566` and the
Terraform AWS provider points to it with an `endpoints {}` block and dummy `test` credentials.
For real AWS I would remove that block and the dummy keys, use real credentials and a real AMI ID.

Tools: Terraform v1.16.4, hashicorp/aws v6.67.0, AWS CLI 2.34, Docker, Graphviz (for `terraform graph` -> PNG).
