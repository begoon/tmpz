provider "aws" {
  region = var.region
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.function_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "lambda" {
  name = "${var.function_name}-lambda-policy"
  role = aws_iam_role.lambda_role.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}


resource "aws_lambda_function" "lambda" {
  filename         = "../../${var.function_zip}"
  function_name    = "bot"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = filebase64sha256("../../${var.function_zip}")

  publish = true

  environment {
    variables = {
      BOT_TOKEN             = var.BOT_TOKEN
      TELEGRAM_SECRET_TOKEN = var.TELEGRAM_SECRET_TOKEN
      ADMIN                 = var.ADMIN
      WH                    = var.WH
      WHERE                 = "aws"
      REDIS_HOST            = var.REDIS_HOST
      REDIS_PORT            = var.REDIS_PORT
      REDIS_PASSWORD        = var.REDIS_PASSWORD
      UPDATED_AT            = timestamp()
    }
  }

  runtime = "python3.11"
}

resource "aws_lambda_function_url" "lambda" {
  function_name      = aws_lambda_function.lambda.function_name
  authorization_type = "NONE"
  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["*"]
  }
}

output "function_url" {
  value = aws_lambda_function_url.lambda.function_url
}
