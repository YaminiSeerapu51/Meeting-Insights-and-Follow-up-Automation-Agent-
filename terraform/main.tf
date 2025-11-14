provider "aws" {
  region = var.aws_region
}

# S3 Bucket for storing meeting data
resource "aws_s3_bucket" "meeting_insights" {
  bucket = var.s3_bucket_name
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Name        = "Meeting Insights Storage"
    Environment = "Production"
  }
}

# IAM Policy for EC2 instance
resource "aws_iam_policy" "meeting_insights_policy" {
  name        = "MeetingInsightsPolicy"
  description = "Policy for Meeting Insights application"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.meeting_insights.arn}",
          "${aws_s3_bucket.meeting_insights.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for EC2
resource "aws_iam_role" "ec2_role" {
  name = "MeetingInsightsEC2Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "MeetingInsightsEC2Role"
  }
}

# Attach policies to the IAM role
resource "aws_iam_role_policy_attachment" "meeting_insights_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.meeting_insights_policy.arn
}

# EC2 Instance Profile
resource "aws_iam_instance_profile" "meeting_insights_profile" {
  name = "MeetingInsightsInstanceProfile"
  role = aws_iam_role.ec2_role.name
}

# Security Group for EC2
resource "aws_security_group" "meeting_insights_sg" {
  name        = "meeting-insights-sg"
  description = "Security group for Meeting Insights application"

  # SSH access from anywhere
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "meeting-insights-sg"
  }
}

# EC2 Instance
resource "aws_instance" "meeting_insights" {
  ami                    = var.ami_id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.meeting_insights_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.meeting_insights_profile.name

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              amazon-linux-extras install docker -y
              service docker start
              usermod -a -G docker ec2-user
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              EOF

  tags = {
    Name = "MeetingInsightsApp"
  }
}

# Output the S3 bucket name
output "s3_bucket_name" {
  value = aws_s3_bucket.meeting_insights.id
}

# Output the EC2 public IP
output "ec2_public_ip" {
  value = aws_instance.meeting_insights.public_ip
}
