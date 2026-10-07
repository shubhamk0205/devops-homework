variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used in resource names."
  type        = string
  default     = "helpdesk"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.21.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnets (one per AZ) - load balancers / NAT gateway."
  type        = list(string)
  default     = ["10.21.1.0/24", "10.21.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnets (one per AZ) - Kubernetes worker nodes."
  type        = list(string)
  default     = ["10.21.11.0/24", "10.21.12.0/24"]
}

variable "availability_zones" {
  description = "Two AZs for high availability."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "backup_bucket_name" {
  description = "S3 bucket for database backups (globally unique on real AWS)."
  type        = string
  default     = "shubham-session21-helpdesk-backups"
}

variable "enable_eks" {
  description = "Create the EKS cluster + node group. false on LocalStack (EKS is not in the free LocalStack edition)."
  type        = bool
  default     = false
}

variable "eks_version" {
  description = "Kubernetes version of the EKS cluster."
  type        = string
  default     = "1.33"
}

variable "node_instance_type" {
  description = "EC2 instance type of the worker nodes."
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Number of worker nodes."
  type        = number
  default     = 2
}
