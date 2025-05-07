# Software Design Specification: `aws-sensor-prep.py`

## Overview
The `aws-sensor-prep.py` script is designed to automate the preparation of AWS IoT resources for LoRaWAN sensors. It includes creating IAM roles, Lambda functions, IoT rules, and configuring permissions to enable seamless integration between AWS IoT Core and Lambda.

---

## Features
1. **IAM Role Creation**:
   - Creates an IAM role with necessary trust and permission policies for Lambda and IoT services.
   - Attaches AWS-managed policies and custom IoT publish permissions.

2. **Lambda Function Management**:
   - Reads and modifies Lambda function code from a local file (`aws-am308-decoder.js`).
   - Packages and uploads the Lambda function to AWS.
   - Configures the Lambda function to handle IoT events.

3. **IoT Rule Creation**:
   - Creates an IoT rule to trigger the Lambda function based on specific MQTT topics.

4. **Permission Configuration**:
   - Adds permissions to allow IoT Core to invoke the Lambda function.

---

## Input Parameters
- **AWS Credentials**:
  - `AWS_ACCESS_KEY`: AWS access key for authentication.
  - `AWS_SECRET_KEY`: AWS secret key for authentication.
  - `REGION`: AWS region where resources will be created.

- **Dynamic Parameters**:
  - `RULE_NAME`: Name of the IoT rule and Lambda function (default: `am308_device_rule_autobot_dev`).

---

## Output
- **Created Resources**:
  - IAM Role: `LambdaExecutionRoleCreateByAutobot`
  - Lambda Function: Named after `RULE_NAME`.
  - IoT Rule: Named after `RULE_NAME`.

- **Logs**:
  - Success or failure messages for each step, including resource ARNs and IDs.

---

## Workflow
1. **Read Lambda Function Code**:
   - Reads the local file `aws-am308-decoder.js`.
   - Replaces placeholders with the IoT endpoint and region.

2. **Create IAM Role**:
   - Checks if the role exists; if not, creates it.
   - Attaches necessary policies for Lambda and IoT access.

3. **Create Lambda Function**:
   - Packages the modified Lambda code into a ZIP file.
   - Uploads the ZIP file to AWS Lambda.

4. **Add Lambda Trigger Permission**:
   - Configures permissions to allow IoT Core to invoke the Lambda function.

5. **Create IoT Rule**:
   - Creates an IoT rule to trigger the Lambda function based on MQTT messages.

---

## Error Handling
- **File Not Found**:
  - If `aws-am308-decoder.js` is missing, the script logs an error and exits.
- **Resource Conflicts**:
  - If a resource (e.g., Lambda function or IoT rule) already exists, the script logs a warning and skips creation.
- **AWS API Errors**:
  - Logs detailed error messages for any AWS API failures.

---

## Dependencies
- **Python Libraries**:
  - `boto3`: AWS SDK for Python.
  - `zipfile`, `io`: For packaging Lambda function code.
  - `time`: For delays to ensure resource availability.

- **AWS Services**:
  - IAM, Lambda, IoT Core.

---

## Security Considerations
- **Credentials**:
  - Avoid hardcoding AWS credentials; use environment variables or IAM roles instead.
- **Permissions**:
  - Ensure least privilege by limiting IAM role permissions to only required actions.

---

This specification provides a clear understanding of the script's functionality, inputs, outputs, and workflow.
