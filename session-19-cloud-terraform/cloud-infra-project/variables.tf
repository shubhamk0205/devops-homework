variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used in resource names."
  type        = string
  default     = "session19"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block of the public subnet."
  type        = string
  default     = "10.20.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "Only this CIDR can SSH to the EC2 instance."
  type        = string
  default     = "0.0.0.0/0"
}

variable "ami_id" {
  description = "AMI used for the EC2 instance."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "bucket_name" {
  description = "Name of the S3 bucket (globally unique on real AWS)."
  type        = string
}
