variable "function_name" { type = string }
variable "source_file"   { type = string }
variable "table_arn"     { type = string }
variable "table_name"    { type = string }

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = var.source_file
  output_path = "${path.module}/app.zip"
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17", Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy" "dynamodb" {
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:PutItem"], Resource = var.table_arn }]
  })
}

resource "aws_lambda_function" "api_handler" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  handler       = "app.handler"
  runtime       = "python3.12"
  environment { variables = { TABLE_NAME = var.table_name } }
}

output "invoke_arn" { value = aws_lambda_function.api_handler.invoke_arn }
output "function_name" { value = aws_lambda_function.api_handler.function_name }