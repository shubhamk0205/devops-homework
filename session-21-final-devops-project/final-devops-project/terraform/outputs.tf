output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value       = aws_subnet.private[*].id
}

output "nat_gateway_id" {
  description = "ID of the NAT gateway."
  value       = aws_nat_gateway.main.id
}

output "nodes_security_group_id" {
  description = "Security group of the worker nodes."
  value       = aws_security_group.nodes.id
}

output "backup_bucket" {
  description = "S3 bucket for database backups."
  value       = aws_s3_bucket.backups.bucket
}

output "eks_cluster_role_arn" {
  description = "IAM role used by the EKS control plane."
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_cluster_name" {
  description = "EKS cluster name (null when enable_eks = false)."
  value       = var.enable_eks ? aws_eks_cluster.main[0].name : null
}

output "kubeconfig_command" {
  description = "Command to point kubectl at the EKS cluster."
  value       = var.enable_eks ? "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main[0].name}" : "EKS disabled (enable_eks = false)"
}
