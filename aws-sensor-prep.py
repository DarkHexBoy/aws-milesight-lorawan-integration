# Create IAM role and configure permissions  
# Create Lambda function  
# Configure Lambda trigger permissions  
# Create IoT Rule  
# Preprocessing complete  

import boto3  
import json  
import zipfile  
import io  
import time  
import json  

# AWS credentials  
AWS_ACCESS_KEY = "not showing you"  
AWS_SECRET_KEY = "not showing you"  
REGION = "us-east-1"  

# Initialize AWS clients  
session = boto3.Session(  
    aws_access_key_id=AWS_ACCESS_KEY,  
    aws_secret_access_key=AWS_SECRET_KEY,  
    region_name=REGION  
)  

# rule_name = "am308_device_rule_autobot"  
RULE_NAME = "am308_device_rule_autobot_dev"   # This is passed dynamically, will optimize later  

# Create Lambda, IoT and IoT Events clients  
lambda_client = session.client("lambda")  
iot_client = session.client("iot")  # Use IoT client to get IoT endpoint  
iot_events_client = session.client("iotevents")  # Use IoT Events client to create target  
iam_client = session.client('iam')  

# Get IoT endpoint info (used in read_lambda_function_code)  
def get_iot_endpoint():  
    try:  
        # Call describe_endpoint to get IoT endpoint, specify endpointType  
        response = iot_client.describe_endpoint(  
            endpointType='iot:Data-ATS'  # Use IoT data endpoint type  
        )  
        # Extract endpointAddress and prepend https://  
        endpoint_address = response['endpointAddress']  
        endpoint_url = f"https://{endpoint_address}"  
        print(f"✅ Retrieved IoT Endpoint: {endpoint_url}")  
        return endpoint_url  
    except Exception as e:  
        print(f"❌ Failed to get IoT Endpoint: {str(e)}")  
        return None  

# Read Lambda function code from local file (assume file aws-am308-decoder.js is in current dir)  
def read_lambda_function_code():  
    endpoint = get_iot_endpoint()  
    if not endpoint:  
        print("❌ Cannot get IoT endpoint, cannot proceed with reading Lambda function code")  
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

# Wait for role to become assumable by Lambda  
def wait_for_role_to_be_assumable(role_name):  
    iam_client.get_waiter('role_exists').wait(RoleName=role_name)  
    print(f"✅ Role {role_name} is ready and can be assumed by Lambda")  

# Create IAM role for Lambda execution  
def create_lambda_execution_role():  
    role_name = 'LambdaExecutionRoleCreateByAutobot'  
    try:  
        # Check if role exists  
        response = iam_client.get_role(RoleName=role_name)  
        role_arn = response['Role']['Arn']  
        print(f"✅ IAM role already exists: {role_arn}")  
    except iam_client.exceptions.NoSuchEntityException:  
        # Role does not exist, create it  
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

        # Wait to ensure role is active  
        print("⏳ Waiting for role to become active...")  
        time.sleep(10)  # Pause 10 seconds to ensure trust policy takes effect  

        # Wait for role to be assumable  
        wait_for_role_to_be_assumable(role_name)  

        # Attach AWS managed policies  
        iam_client.attach_role_policy(  
            RoleName=role_name,  
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Basic Lambda execution permission  
        )  
        iam_client.attach_role_policy(  
            RoleName=role_name,  
            PolicyArn="arn:aws:iam::aws:policy/AWSIoTDataAccess"  # IoT access permission  
        )  

        # Add custom IoT publish permission  
        iot_publish_policy = {  
            "Version": "2012-10-17",  
            "Statement": [  
                {  
                    "Effect": "Allow",  
                    "Action": [  
                        "iot:Publish",  
                        "iot:DescribeEndpoint"],  
                    "Resource": ["*"]  # Allow publishing to all IoT topics  
                }  
            ]  
        }  
        iam_client.put_role_policy(  
            RoleName=role_name,  
            PolicyName="IoTPublishPolicy",  
            PolicyDocument=json.dumps(iot_publish_policy)  
        )  

        print("✅ Permission policies attached to role")  

    return role_arn  

# Package and upload Lambda function code  
def create_lambda_function(role_arn, lambda_function_code):  
    zip_buffer = io.BytesIO()  
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:  
        # Important: filename must end with .mjs, not .js  
        zf.writestr("lambda_function.mjs", lambda_function_code)  
    
    zip_buffer.seek(0)  

    try:  
        response = lambda_client.create_function(  
            FunctionName=RULE_NAME,  # Lambda function name  
            Runtime="nodejs20.x",  # Node.js 20.x runtime  
            Role=role_arn,  # Use the created IAM role  
            Handler="lambda_function.handler",  # Lambda entry point  
            Code={"ZipFile": zip_buffer.read()},  
            Timeout=60,  # Timeout setting  
            MemorySize=128  # Memory setting  
        )  
        lambda_arn = response["FunctionArn"]  
        print(f"✅ Lambda function created successfully: {lambda_arn}")  
        return lambda_arn  
    except lambda_client.exceptions.ResourceConflictException:  
        print("⚠️ Lambda function already exists, skipping creation")  
        # If function exists, return existing ARN  
        response = lambda_client.get_function(FunctionName=RULE_NAME)  
        return response['Configuration']['FunctionArn']  
    except Exception as e:  
        print(f"❌ Lambda function creation failed: {str(e)}")  
        return None  

# Add IoT trigger permission for Lambda  
def add_lambda_trigger_permission(lambda_arn):  
    try:  
        lambda_client.add_permission(  
            FunctionName=RULE_NAME,  
            StatementId="AllowIoTInvoke",  # Ensure StatementId is unique  
            Action="lambda:InvokeFunction",  
            Principal="iot.amazonaws.com",  
            SourceArn=f"arn:aws:iot:{REGION}:{session.client('sts').get_caller_identity()['Account']}:rule/{RULE_NAME}",  
        )  
        print("✅ Successfully added Lambda trigger permission")  
    except lambda_client.exceptions.ResourceConflictException:  
        print("⚠️ Trigger permission already exists, skipping")  
    except Exception as e:  
        print(f"❌ Failed to add Lambda trigger permission: {str(e)}")  

# Create IoT topic rule  
def create_iot_topic_rule(lambda_arn):  
    try:  
        # Try creating IoT rule  
        response = iot_client.create_topic_rule(  
            ruleName=RULE_NAME,  # Rule name  
            topicRulePayload={  
                "sql": "SELECT *",  # SQL query condition  
                "actions": [  
                    {  
                        "lambda": {  
                            "functionArn": lambda_arn  # Lambda ARN  
                        }  
                    }  
                ],  
                "ruleDisabled": False  # Enable rule  
            }  
        )  
        print(f"✅ IoT rule created successfully")  
    except iot_client.exceptions.ResourceAlreadyExistsException:  
        print(f"⚠️ IoT rule '{RULE_NAME}' already exists, skipping creation")  
    except Exception as e:  
        print(f"❌ Failed to create IoT rule: {str(e)}")  

# Execute workflow  
lambda_function_code = read_lambda_function_code()  # Read Lambda function code and replace placeholders  
if lambda_function_code:  
    role_arn = create_lambda_execution_role()  # Create or get IAM role  
    if role_arn:  
        lambda_arn = create_lambda_function(role_arn, lambda_function_code)  # Create Lambda function  
        if lambda_arn:  
            add_lambda_trigger_permission(lambda_arn)  # Add trigger permission to Lambda  
            create_iot_topic_rule(lambda_arn)  # Create IoT rule and bind Lambda function  
            print(f"✅ IoT preprocessing completed, {RULE_NAME} created successfully")  
