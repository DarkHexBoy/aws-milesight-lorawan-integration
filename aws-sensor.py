
# filename: aws-sensor.py
# function: 创建 sensor 并且关联 lambda 触发

import boto3
import time

# AWS 认证信息
AWS_ACCESS_KEY = "不给你看"
AWS_SECRET_KEY = "不给你看"
REGION = "us-east-1"

# LoRaWAN 设备 OTAA 参数
DEVICE_EUI = "24E124707E043923"
APP_EUI = "24E124707E043923"
APP_KEY = "5572404C696E6B4C6F52613230889012"
DEVICE_NAME = "am308-lockon-demo"

# 目标 Profile 名称（用于匹配已有 Profile）
DEVICE_PROFILE_NAME = "US915-A-OTAA"
SERVICE_PROFILE_NAME = "AM308-Profile"
DESTINATION_NAME = "am308-destination-autobot-dev"  # Destination 名称
ROLE_NAME = "LambdaExecutionRoleCreateByAutobot"  # 从 aws-sensor.py 那边获取过来就行了
RULE_NAME = "am308_device_rule_autobot_dev"

# 初始化 AWS IoT Wireless 客户端
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)
client = session.client("iotwireless")
iot_client = session.client("iot")  # 用于获取 IAM 角色 ARN


# **Step 1: 获取 IAM 角色 ARN**
def get_role_arn(role_name=ROLE_NAME):
    sts_client = session.client("sts")
    try:
        # 获取 AWS 账户 ID
        account_id = sts_client.get_caller_identity()["Account"]
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"✅ 角色 ARN 获取成功: {role_arn}")
        return role_arn
    except Exception as e:
        print(f"❌ 获取角色 ARN 失败: {str(e)}")
        return None


# **Step 2: 创建 Device Profile**
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
        print(f"✅ 设备配置文件创建成功: {profile_id}")
        return profile_id
    except Exception as e:
        print(f"❌ 设备配置文件创建失败: {str(e)}")
        return None


# **Step 3: 创建 Service Profile（如果不存在）**
def create_service_profile():
    try:
        response = client.create_service_profile(
            Name=SERVICE_PROFILE_NAME,
            LoRaWAN={
                "AddGwMetadata": True
            }
        )
        service_id = response["Id"]
        print(f"✅ 服务配置文件创建成功: {service_id}")
        return service_id
    except Exception as e:
        print(f"❌ 服务配置文件创建失败: {str(e)}")
        return None


# **Step 4: 创建 LoRaWAN 设备**
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
        print(f"✅ LoRaWAN 设备创建成功，设备 ID: {device_id}")
    except Exception as e:
        print(f"❌ LoRaWAN 设备创建失败: {str(e)}")


# **Step 5: 创建 Destination**
def create_destination(role_arn):
    try:
        # 尝试创建 Destination
        response = client.create_destination(
            Name=DESTINATION_NAME,  # 使用 Name 而不是 destinationName
            ExpressionType="RuleName",  # 确保 ExpressionType 为 RuleName
            Expression=RULE_NAME,  # 传入规则名称，从 aws-seosor-prep.py 那边获取
            RoleArn=role_arn,  # 关联 IAM 角色 ARN
            Tags=[]  # 可选参数，您可以留空或者根据需求添加标签
        )
        print(response)  # 打印响应，检查是否包含 'Name'
        destination_name = response["Name"]  # 获取 'Name' 字段
        print(f"✅ Destination 创建成功: {destination_name}")
        return destination_name  # 返回名称而非 ID

    except client.exceptions.ConflictException as e:
        # 如果已存在相同名称的 Destination，则跳过创建
        print(f"⚠️ Destination 已存在，跳过创建: {e}")
        return DESTINATION_NAME  # 返回现有的 Destination 名称

    except Exception as e:
        print(f"❌ Destination 创建失败: {str(e)}")
        return None





# **执行流程**
role_arn = get_role_arn()  # 获取 IAM 角色 ARN
if role_arn:
    destination_id = create_destination(role_arn)  # 创建 Destination
    time.sleep(2)  # 确保 Destination 创建成功

    device_profile_id = create_device_profile()  # 创建设备配置文件
    time.sleep(2)  # 确保创建成功

    service_profile_id = create_service_profile()  # 创建服务配置文件
    time.sleep(2)  # 确保创建成功

    if device_profile_id and service_profile_id and destination_id:
        create_lorawan_device(device_profile_id, service_profile_id)  # 创建设备
    else:
        print("❌ 无法创建 LoRaWAN 设备，缺少 Profile ID 或 Destination ID")
else:
    print("❌ 无法获取 IAM 角色 ARN")
