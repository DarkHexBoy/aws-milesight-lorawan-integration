# Create IAM role and configure permissions
# Create Lambda function
# Configure Lambda trigger permissions
# Create IoT rule
# Preprocessing complete

import boto3
import json
import zipfile
import io
import time
import json

# AWS credentials
AWS_ACCESS_KEY = "xxxx"
AWS_SECRET_KEY = "xxxx"
REGION = "us-east-1"

# Initialize AWS client
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# rule_name = "am308_device_rule_autobot"
RULE_NAME = "am308_device_rule_autobot_dev"   # This is a dynamically passed parameter, to be optimized later

# Create Lambda, IoT, and IoT Events clients
lambda_client = session.client("lambda")
iot_client = session.client("iot")  # Use IoT client to get IoT endpoint
iot_events_client = session.client("iotevents")  # Use IoT Events client to create targets
iam_client = session.client('iam')

# Get IoT endpoint information (mainly used in read_lambda_function_code)
def get_iot_endpoint():
    try:
        # Call describe_endpoint to get IoT Endpoint information, specify endpointType
        response = iot_client.describe_endpoint(
            endpointType='iot:Data-ATS'  # Use IoT data stream endpoint type
        )
        # Extract endpointAddress and prepend https://
        endpoint_address = response['endpointAddress']
        endpoint_url = f"https://{endpoint_address}"
        print(f"✅ IoT Endpoint retrieved: {endpoint_url}")
        return endpoint_url
    except Exception as e:
        print(f"❌ Failed to retrieve IoT Endpoint: {str(e)}")
        return None


# Read Lambda function code from local file (assuming aws-am308-decoder.js is in the current directory)
def read_lambda_function_code():
    endpoint = get_iot_endpoint()
    if not endpoint:
        print("❌ Unable to retrieve IoT endpoint, cannot proceed to read Lambda function code")
        return None
    
    try:
        # Read Lambda function code
        with open("aws-am308-decoder.js", "r", encoding="utf-8") as file:
            code = file.read()
        
        # Replace placeholders
        code = code.replace("{$FILL YOUR ENDPOINT$}", endpoint)
        code = code.replace("{$REGION$}", REGION)
        
        return code
    except FileNotFoundError:
        print("❌ Lambda function file not found")
        return None
    except Exception as e:
        print(f"❌ Failed to read Lambda function code: {str(e)}")
        return None



def wait_for_role_to_be_assumable(role_name):
    """Wait for the role to be assumable by Lambda"""
    iam_client.get_waiter('role_exists').wait(RoleName=role_name)
    print(f"✅ Role {role_name} is ready and can be assumed by Lambda")

def create_lambda_execution_role():
    role_name = 'LambdaExecutionRoleCreateByAutobot'
    try:
        # Check if the role exists
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ IAM role already exists: {role_arn}")
    except iam_client.exceptions.NoSuchEntityException:
        # Role does not exist, create the role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": [
                            "iotwireless.amazonaws.com",
                            "iot.amazonaws.com",
                            "lambda.amazonaws.com"
                        ]
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Lambda function execution'
        )
        role_arn = response['Role']['Arn']
        print(f"✅ IAM role created successfully: {role_arn}")

        # Delay for a while to ensure the role is fully effective
        print("⏳ Waiting for the role to take effect...")
        time.sleep(10)  # Pause for 10 seconds to ensure the trust policy is effective

        # Wait for the role to be assumable by Lambda
        wait_for_role_to_be_assumable(role_name)

        # Attach AWS official policies
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Basic Lambda execution permissions
        )
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AWSIoTDataAccess"  # IoT access permissions
        )

        # Add custom IoT Publish permissions
        iot_publish_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Publish",
                        "iot:DescribeEndpoint"
                    ],
                    "Resource": ["*"]  # Allow publishing to all IoT topics
                }
            ]
        }
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="IoTPublishPolicy",
            PolicyDocument=json.dumps(iot_publish_policy)
        )

        print("✅ Permissions attached to the role")

    return role_arn



# Package and upload Lambda function code
def create_lambda_function(role_arn, lambda_function_code):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Note: The file extension must be mjs, not js
        zf.writestr("lambda_function.mjs", lambda_function_code)  
    
    zip_buffer.seek(0)

    try:
        response = lambda_client.create_function(
            FunctionName=RULE_NAME,  # Modified Lambda function name
            Runtime="nodejs20.x",  # Use Node.js version 20.x
            Role=role_arn,  # Use the automatically created IAM role
            Handler="lambda_function.handler",  # Node.js Lambda function entry point
            Code={"ZipFile": zip_buffer.read()},
            Timeout=60,  # Timeout setting
            MemorySize=128  # Memory setting
        )
        lambda_arn = response["FunctionArn"]
        print(f"✅ Lambda function created successfully: {lambda_arn}")
        return lambda_arn
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️ Lambda function already exists, skipping creation")
        # If the function already exists, return the existing Lambda function ARN
        response = lambda_client.get_function(FunctionName=RULE_NAME)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"❌ Failed to create Lambda function: {str(e)}")
        return None

# Add IoT trigger permissions to Lambda function
def add_lambda_trigger_permission(lambda_arn):
    try:
        lambda_client.add_permission(
            FunctionName=RULE_NAME,
            StatementId="AllowIoTInvoke",  # Ensure StatementId is unique
            Action="lambda:InvokeFunction",
            Principal="iot.amazonaws.com",
            SourceArn=f"arn:aws:iot:{REGION}:{session.client('sts').get_caller_identity()['Account']}:rule/{RULE_NAME}",
        )
        print("✅ Successfully added Lambda trigger permissions")
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️ Trigger permissions already exist, skipping")
    except Exception as e:
        print(f"❌ Failed to add Lambda trigger permissions: {str(e)}")

# Create IoT rule
def create_iot_topic_rule(lambda_arn):
    try:
        # Attempt to create IoT rule
        response = iot_client.create_topic_rule(
            ruleName=RULE_NAME,  # Rule name
            topicRulePayload={
                "sql": "SELECT *",  # SQL query condition
                "actions": [
                    {
                        "lambda": {
                            "functionArn": lambda_arn  # Specify the Lambda function ARN
                        }
                    }
                ],
                "ruleDisabled": False  # Enable the rule
            }
        )
        print(f"✅ IoT rule created successfully")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        # If the rule already exists, output information and skip creation
        print(f"⚠️ IoT rule '{RULE_NAME}' already exists, skipping")
    except Exception as e:
        print(f"❌ Failed to create IoT rule: {str(e)}")


# Execution flow
lambda_function_code = read_lambda_function_code()  # Read Lambda function code from local file and replace placeholders
if lambda_function_code:
    role_arn = create_lambda_execution_role()  # Automatically create IAM role or retrieve existing role
    if role_arn:
        lambda_arn = create_lambda_function(role_arn, lambda_function_code)  # Use the role to create Lambda function
        if lambda_arn:
            add_lambda_trigger_permission(lambda_arn)  # Add trigger permissions to Lambda
            create_iot_topic_rule(lambda_arn)  # Create IoT rule and bind Lambda function
            print(f"✅ IoT preprocessing complete, {RULE_NAME} created successfully")


