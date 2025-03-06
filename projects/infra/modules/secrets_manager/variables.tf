# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Secrets Manager variables

variable "secret_name" {
  description = "Name of the secret in AWS Secrets Manager"
  type        = string
  default     = "jwt-secret-key"
}

variable "description" {
  description = "Description of the secret"
  type        = string
  default     = "Secret key for JWT token generation"
}

variable "recovery_window_in_days" {
  description = "Number of days that AWS Secrets Manager waits before it can delete the secret"
  type        = number
  default     = 0
}

variable "generate_random_secret" {
  description = "Whether to generate a random secret or use a provided one"
  type        = bool
  default     = true
}

variable "provided_secret_key" {
  description = "The secret key to use if not generating a random one"
  type        = string
  default     = ""
  sensitive   = true
}
