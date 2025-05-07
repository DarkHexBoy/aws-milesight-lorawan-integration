# Software Design Specification: `aws-sensor.py`

## Overview
The `aws-sensor.py` script automates the creation and registration of LoRaWAN sensors in AWS IoT Core. It handles the creation of device profiles, service profiles, destinations, and the registration of LoRaWAN devices.

---

## Features
1. **IAM Role Retrieval**:
   - Retrieves the ARN of an existing IAM role required for associating destinations.

2. **Device Profile Creation**:
   - Creates a device profile for LoRaWAN devices with specific configurations.

3. **Service Profile Creation**:
   - Creates a service profile for LoRaWAN devices to define service-level configurations.

4. **Destination Creation**:
   - Creates a destination in AWS IoT Core to route messages from LoRaWAN devices to specific rules.

5. **LoRaWAN Device Registration**:
   - Registers a LoRaWAN device with OTAA (Over-The-Air Activation) parameters.

---

## Input Parameters
- **AWS Credentials**:
  - `AWS_ACCESS_KEY`: AWS access key for authentication.
  - `AWS_SECRET_KEY`: AWS secret key for authentication.
  - `REGION`: AWS region where resources will be created.

- **LoRaWAN Device Parameters**:
  - `DEVICE_EUI`: Device EUI for OTAA.
  - `APP_EUI`: Application EUI for OTAA.
  - `APP_KEY`: Application Key for OTAA.
  - `DEVICE_NAME`: Name of the LoRaWAN device.

- **Profile and Destination Parameters**:
  - `DEVICE_PROFILE_NAME`: Name of the device profile.
  - `SERVICE_PROFILE_NAME`: Name of the service profile.
  - `DESTINATION_NAME`: Name of the destination.
  - `ROLE_NAME`: Name of the IAM role.
  - `RULE_NAME`: Name of the IoT rule.

---

## Output
- **Created Resources**:
  - Device Profile: ID of the created device profile.
  - Service Profile: ID of the created service profile.
  - Destination: Name of the created destination.
  - LoRaWAN Device: ID of the registered device.

- **Logs**:
  - Success or failure messages for each step, including resource IDs and ARNs.

---

## Workflow
1. **Retrieve IAM Role ARN**:
   - Retrieves the ARN of the IAM role specified by `ROLE_NAME`.

2. **Create Destination**:
   - Creates a destination in AWS IoT Core and associates it with the specified IoT rule.

3. **Create Device Profile**:
   - Creates a device profile with LoRaWAN-specific configurations.

4. **Create Service Profile**:
   - Creates a service profile for LoRaWAN devices.

5. **Register LoRaWAN Device**:
   - Registers a LoRaWAN device with the created profiles and destination.

---

## Error Handling
- **AWS API Errors**:
  - Logs detailed error messages for any AWS API failures.
- **Resource Conflicts**:
  - If a resource (e.g., destination) already exists, the script logs a warning and skips creation.

---

## Dependencies
- **Python Libraries**:
  - `boto3`: AWS SDK for Python.
  - `time`: For delays to ensure resource availability.

- **AWS Services**:
  - IAM, IoT Core.

---

## Security Considerations
- **Credentials**:
  - Avoid hardcoding AWS credentials; use environment variables or IAM roles instead.
- **Permissions**:
  - Ensure least privilege by limiting IAM role permissions to only required actions.

---

This specification provides a clear understanding of the script's functionality, inputs, outputs, and workflow.
