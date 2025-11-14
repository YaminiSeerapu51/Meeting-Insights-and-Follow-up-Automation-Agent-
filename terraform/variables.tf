variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for storing meeting data"
  type        = string
  default     = "meeting-insights-bucket-${random_id.bucket_suffix.hex}"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0c55b159cbfafe1f0" # Amazon Linux 2 AMI (HVM), SSD Volume Type
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}
