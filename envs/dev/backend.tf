terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "tf-state-lab3-herasymenko-vadym-05" # Твій бакет з 3-ї лаби [cite: 558]
    key          = "envs/dev/lab4.tfstate"              # Окремий шлях для 4-ї лаби [cite: 587]
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true                                 # Нова фіча для блокування стану [cite: 590]
  }
}