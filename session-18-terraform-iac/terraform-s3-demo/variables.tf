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
