# 创建 iam 角色，并且配置权限
# 创建 lambda 函数
# 配置 lambda 的触发权限
# 创建 rule 
# 预处理结束

import boto3
import json
import zipfile
import io
import time
import json

# AWS 认证信息
AWS_ACCESS_KEY = "不给你看"
AWS_SECRET_KEY = "不给你看"
REGION = "us-east-1"

# 初始化 AWS 客户端
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# rule_name = "am308_device_rule_autobot"
RULE_NAME = "am308_device_rule_autobot_dev"   # 属于动态传递进来的参数，优化时候再改

# 创建 Lambda、IoT 和 IoT Events 客户端
lambda_client = session.client("lambda")
iot_client = session.client("iot")  # 用 iot 客户端来获取 IoT 端点
iot_events_client = session.client("iotevents")  # 使用 IoT Events 客户端来创建目标
iam_client = session.client('iam')

# 获取 IoT 端点信息(主要是在 read_lambda_function_code 读出来的内容)
def get_iot_endpoint():
    try:
        # 调用 describe_endpoint 获取 IoT Endpoint 信息，指定 endpointType
        response = iot_client.describe_endpoint(
            endpointType='iot:Data-ATS'  # 使用 IoT 数据流端点类型
        )
        # 提取 endpointAddress 并拼接 https:// 前缀
        endpoint_address = response['endpointAddress']
        endpoint_url = f"https://{endpoint_address}"
        print(f"✅ 获取到的 IoT Endpoint: {endpoint_url}")
        return endpoint_url
    except Exception as e:
        print(f"❌ 获取 IoT Endpoint 失败: {str(e)}")
        return None


# 从本地读取 Lambda 函数代码（假设文件 aws-am308-decoder.js 在当前目录下）
def read_lambda_function_code():
    endpoint = get_iot_endpoint()
    if not endpoint:
        print("❌ 无法获取 IoT 端点，无法继续读取 Lambda 函数代码")
        return None
    
    try:
        # 读取 Lambda 函数代码
        with open("aws-am308-decoder.js", "r", encoding="utf-8") as file:
            code = file.read()
        
        # 替换占位符
        code = code.replace("{$FILL YOUR ENDPOINT$}", endpoint)
        code = code.replace("{$REGION$}", REGION)
        
        return code
    except FileNotFoundError:
        print("❌ Lambda 函数文件未找到")
        return None
    except Exception as e:
        print(f"❌ 读取 Lambda 函数代码失败: {str(e)}")
        return None



# def create_lambda_execution_role():
#     role_name = 'LambdaExecutionRoleCreateByAutobot'
#     try:
#         # 检查角色是否存在
#         response = iam_client.get_role(RoleName=role_name)
#         role_arn = response['Role']['Arn']
#         print(f"✅ IAM 角色已存在: {role_arn}")
#     except iam_client.exceptions.NoSuchEntityException:
#         # 角色不存在，创建角色
#         trust_policy = {
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Principal": {
#                         "Service": [
#                             "iotwireless.amazonaws.com",  # 添加 iotwireless.amazonaws.com
#                             "iot.amazonaws.com",          # 添加 iot.amazonaws.com
#                             "lambda.amazonaws.com"        # 保持 lambda.amazonaws.com
#                         ]
#                     },
#                     "Action": "sts:AssumeRole"
#                 }
#             ]
#         }

#         response = iam_client.create_role(
#             RoleName=role_name,
#             AssumeRolePolicyDocument=json.dumps(trust_policy),
#             Description='Role for Lambda function execution'
#         )
#         role_arn = response['Role']['Arn']
#         print(f"✅ IAM 角色创建成功: {role_arn}")

#         # 延迟一段时间，确保角色已完全生效
#         print("⏳ 等待角色生效...")
#         time.sleep(15)  # 暂停 15 秒钟，确保角色的信任策略已经生效

#         # 附加 AWS 官方策略
#         iam_client.attach_role_policy(
#             RoleName=role_name,
#             PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Lambda 基本执行权限
#         )
#         iam_client.attach_role_policy(
#             RoleName=role_name,
#             PolicyArn="arn:aws:iam::aws:policy/AWSIoTDataAccess"  # IoT 访问权限
#         )

#         # **单独添加 IoT Publish 权限**
#         iot_publish_policy = {
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Action": ["iot:Publish"],
#                     "Resource": ["*"]  # 允许对所有 IoT 主题发布消息
#                 }
#             ]
#         }
#         iam_client.put_role_policy(
#             RoleName=role_name,
#             PolicyName="IoTPublishPolicy",
#             PolicyDocument=json.dumps(iot_publish_policy)
#         )

#         print("✅ 权限策略已附加到角色")

#     return role_arn


def wait_for_role_to_be_assumable(role_name):
    """等待角色可以被 Lambda 假设"""
    iam_client.get_waiter('role_exists').wait(RoleName=role_name)
    print(f"✅ 角色 {role_name} 已经准备好，能够被 Lambda 假设")

def create_lambda_execution_role():
    role_name = 'LambdaExecutionRoleCreateByAutobot'
    try:
        # 检查角色是否存在
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ IAM 角色已存在: {role_arn}")
    except iam_client.exceptions.NoSuchEntityException:
        # 角色不存在，创建角色
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
        print(f"✅ IAM 角色创建成功: {role_arn}")

        # 延迟一段时间，确保角色已完全生效
        print("⏳ 等待角色生效...")
        time.sleep(10)  # 暂停 10 秒钟，确保角色的信任策略已经生效

        # 等待角色可以被 Lambda 假设
        wait_for_role_to_be_assumable(role_name)

        # 附加 AWS 官方策略
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Lambda 基本执行权限
        )
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AWSIoTDataAccess"  # IoT 访问权限
        )

        # **单独添加 IoT Publish 权限**
        iot_publish_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Publish",
                        "iot:DescribeEndpoint"],
                    "Resource": ["*"]  # 允许对所有 IoT 主题发布消息
                }
            ]
        }
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="IoTPublishPolicy",
            PolicyDocument=json.dumps(iot_publish_policy)
        )

        print("✅ 权限策略已附加到角色")

    return role_arn



# **将 Lambda 函数代码打包并上传**
def create_lambda_function(role_arn, lambda_function_code):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 注意这里的后缀名，一定要 mjs 后缀，不能用 js
        zf.writestr("lambda_function.mjs", lambda_function_code)  
    
    zip_buffer.seek(0)

    try:
        response = lambda_client.create_function(
            FunctionName=RULE_NAME,  # 修改了 Lambda 函数名称
            Runtime="nodejs20.x",  # 使用 Node.js 版本 20.x
            Role=role_arn,  # 使用自动创建的 IAM 角色
            Handler="lambda_function.handler",  # Node.js Lambda 函数入口
            Code={"ZipFile": zip_buffer.read()},
            Timeout=60,  # 超时设置
            MemorySize=128  # 内存设置
        )
        lambda_arn = response["FunctionArn"]
        print(f"✅ Lambda 函数创建成功: {lambda_arn}")
        return lambda_arn
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️ Lambda 函数已存在，跳过创建")
        # 如果函数已存在，则返回现有的 Lambda 函数 ARN
        response = lambda_client.get_function(FunctionName=RULE_NAME)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"❌ Lambda 函数创建失败: {str(e)}")
        return None

# **为 Lambda 函数添加 IoT 触发权限**
def add_lambda_trigger_permission(lambda_arn):
    try:
        lambda_client.add_permission(
            FunctionName=RULE_NAME,
            StatementId="AllowIoTInvoke",  # 确保 StatementId 是唯一的
            Action="lambda:InvokeFunction",
            Principal="iot.amazonaws.com",
            SourceArn=f"arn:aws:iot:{REGION}:{session.client('sts').get_caller_identity()['Account']}:rule/{RULE_NAME}",
        )
        print("✅ 成功添加 Lambda 触发权限")
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️ 触发权限已存在，跳过添加")
    except Exception as e:
        print(f"❌ 添加 Lambda 触发权限失败: {str(e)}")

# **创建 IoT 规则**
def create_iot_topic_rule(lambda_arn):
    try:
        # 尝试创建 IoT 规则
        response = iot_client.create_topic_rule(
            ruleName=RULE_NAME,  # 规则名称
            topicRulePayload={
                "sql": "SELECT *",  # SQL 查询条件
                "actions": [
                    {
                        "lambda": {
                            "functionArn": lambda_arn  # 指定 Lambda 函数的 ARN
                        }
                    }
                ],
                "ruleDisabled": False  # 启用规则
            }
        )
        print(f"✅ IoT 规则创建成功")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        # 如果规则已经存在，输出信息并跳过创建
        print(f"⚠️ IoT 规则 '{RULE_NAME}' 已存在，跳过创建")
    except Exception as e:
        print(f"❌ IoT 规则创建失败: {str(e)}")


# **执行流程**
lambda_function_code = read_lambda_function_code()  # 从本地读取 Lambda 函数代码并替换占位符
if lambda_function_code:
    role_arn = create_lambda_execution_role()  # 自动创建 IAM 角色或获取已存在的角色
    if role_arn:
        lambda_arn = create_lambda_function(role_arn, lambda_function_code)  # 使用角色创建 Lambda 函数
        if lambda_arn:
            add_lambda_trigger_permission(lambda_arn)  # 为 Lambda 添加触发权限
            create_iot_topic_rule(lambda_arn)  # 创建 IoT 规则并绑定 Lambda 函数
            print(f"✅ IoT 预处理结束，: {RULE_NAME} 创建成功")


