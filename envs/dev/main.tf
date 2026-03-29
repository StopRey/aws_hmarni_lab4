provider "aws" {
  region = "eu-central-1"
}

locals {
  # Твій унікальний префікс згідно з вимогами [cite: 53, 601]
  prefix = "herasymenko-vadym-05"
}

# 1. Виклик модуля бази даних [cite: 603]
module "database" {
  source     = "../../modules/dynamodb"
  table_name = "${local.prefix}-rates-cache"
}

# 2. Виклик модуля Lambda [cite: 608]
module "backend" {
  source        = "../../modules/lambda"
  function_name = "${local.prefix}-api-handler"
  source_file   = "../../src/app.py" # Шлях до твого коду [cite: 616]
  table_arn     = module.database.table_arn
  table_name    = module.database.table_name
}

# 3. Виклик модуля API Gateway [cite: 619]
module "api" {
  source               = "../../modules/api_gateway"
  api_name             = "${local.prefix}-http-api"
  lambda_invoke_arn    = module.backend.invoke_arn
  lambda_function_name = module.backend.function_name
}

# Вивід URL для тестування [cite: 625]
output "api_url" {
  value = "${module.api.api_endpoint}/rates/{base}"
}