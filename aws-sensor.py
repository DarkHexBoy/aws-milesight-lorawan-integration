# filename: aws-sensor.py
# function: Create sensor and associate lambda trigger

import boto3
import time

# AWS credentials
AWS_ACCESS_KEY = "xxxx"
AWS_SECRET_KEY = "xxxx"
REGION = "us-east-1"

# LoRaWAN device OTAA parameters
DEVICE_EUI = "24E124707E043923"
APP_EUI = "24E124707E043923"
APP_KEY = "5572404C696E6B4C6F52613230889012"
DEVICE_NAME = "am308-lockon-demo"

# Target Profile name (used to match existing Profile)
DEVICE_PROFILE_NAME = "US915-A-OTAA"
SERVICE_PROFILE_NAME = "AM308-Profile"
DESTINATION_NAME = "am308-destination-autobot-dev"  # Destination name
ROLE_NAME = "LambdaExecutionRoleCreateByAutobot"  # Retrieved from aws-sensor.py
RULE_NAME = "am308_device_rule_autobot_dev"

# Initialize AWS IoT Wireless client
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)
client = session.client("iotwireless")
iot_client = session.client("iot")  # Used to retrieve IAM role ARN


# **Step 1: Retrieve IAM role ARN**
def get_role_arn(role_name=ROLE_NAME):
    sts_client = session.client("sts")
    try:
        # Retrieve AWS account ID
        account_id = sts_client.get_caller_identity()["Account"]
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"✅ Successfully retrieved role ARN: {role_arn}")
        return role_arn
    except Exception as e:
        print(f"❌ Failed to retrieve role ARN: {str(e)}")
        return None


# **Step 2: Create Device Profile**
def create_device_profile():
    try:
        response = client.create_device_profile(
            Name=DEVICE_PROFILE_NAME,
            LoRaWAN={
                "MacVersion": "1.0.3",
                "RegParamsRevision": "RP002-1.0.1",
                "SupportsJoin": True
            }
        )
        profile_id = response["Id"]
        print(f"✅ Successfully created device profile: {profile_id}")
        return profile_id
    except Exception as e:
        print(f"❌ Failed to create device profile: {str(e)}")
        return None


# **Step 3: Create Service Profile (if it does not exist)**
def create_service_profile():
    try:
        response = client.create_service_profile(
            Name=SERVICE_PROFILE_NAME,
            LoRaWAN={
                "AddGwMetadata": True
            }
        )
        service_id = response["Id"]
        print(f"✅ Successfully created service profile: {service_id}")
        return service_id
    except Exception as e:
        print(f"❌ Failed to create service profile: {str(e)}")
        return None


# **Step 4: Create LoRaWAN Device**
def create_lorawan_device(device_profile_id, service_profile_id):
    device_params = {
        "Type": "LoRaWAN",
        "Name": DEVICE_NAME,
        "Description": "LoRaWAN Device registered via Python",
        "DestinationName": DESTINATION_NAME,
        "LoRaWAN": {
            "DevEui": DEVICE_EUI,
            "DeviceProfileId": device_profile_id,
            "ServiceProfileId": service_profile_id,
            "OtaaV1_0_x": {
                "AppEui": APP_EUI,
                "AppKey": APP_KEY
            }
        },
    }

    try:
        response = client.create_wireless_device(**device_params)
        device_id = response["Id"]
        print(f"✅ Successfully created LoRaWAN device, Device ID: {device_id}")
    except Exception as e:
        print(f"❌ Failed to create LoRaWAN device: {str(e)}")


# **Step 5: Create Destination**
def create_destination(role_arn):
    try:
        # Attempt to create Destination
        response = client.create_destination(
            Name=DESTINATION_NAME,  # Use Name instead of destinationName
            ExpressionType="RuleName",  # Ensure ExpressionType is RuleName
            Expression=RULE_NAME,  # Pass in rule name, retrieved from aws-sensor-prep.py
            RoleArn=role_arn,  # Associate IAM role ARN
            Tags=[]  # Optional parameter, can be left empty or populated as needed
        )
        print(response)  # Print response to check if it contains 'Name'
        destination_name = response["Name"]  # Retrieve 'Name' field
        print(f"✅ Successfully created Destination: {destination_name}")
        return destination_name  # Return the name instead of the ID

    except client.exceptions.ConflictException as e:
        # If a Destination with the same name already exists, skip creation
        print(f"⚠️ Destination already exists, skipping creation: {e}")
        return DESTINATION_NAME  # Return the existing Destination name

    except Exception as e:
        print(f"❌ Failed to create Destination: {str(e)}")
        return None


# Execution flow
role_arn = get_role_arn()  # Retrieve IAM role ARN
if role_arn:
    destination_id = create_destination(role_arn)  # Create Destination
    time.sleep(2)  # Ensure Destination is successfully created

    device_profile_id = create_device_profile()  # Create Device Profile
    time.sleep(2)  # Ensure successful creation

    service_profile_id = create_service_profile()  # Create Service Profile
    time.sleep(2)  # Ensure successful creation

    if device_profile_id and service_profile_id and destination_id:
        create_lorawan_device(device_profile_id, service_profile_id)  # Create Device
    else:
        print("❌ Unable to create LoRaWAN device, missing Profile ID or Destination ID")
else:
    print("❌ Unable to retrieve IAM role ARN")
