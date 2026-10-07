aws_region         = "us-east-1"
project_name       = "session19"
vpc_cidr           = "10.20.0.0/16"
public_subnet_cidr = "10.20.1.0/24"
allowed_ssh_cidr   = "0.0.0.0/0"
instance_type      = "t3.micro"
bucket_name        = "shubham-session19-app-bucket"

# Amazon Linux AMI from LocalStack's mock image list.
# On real AWS use a current AMI id for your region.
ami_id = "ami-760aaa0f"
