import boto3
import json
import hashlib
import hmac
import requests
import os
import shutil
from datetime import datetime
import configparser

# ================================
# 配置 AWS 认证信息
# ================================
AWS_ACCESS_KEY = "不给你看"
AWS_SECRET_KEY = "不给你看"
REGION = "us-east-1"  # 选择 AWS IoT Core 所在区域
SERVICE = "iotwireless"
HOST = f"{SERVICE}.{REGION}.amazonaws.com"
ENDPOINT = f"https://{HOST}"

# 初始化 AWS 客户端
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)
client = session.client("iotwireless")
iot_client = session.client("iot")

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
config_filename = "aws.ini"

# ================================
# **1. 创建 LoRaWAN 网关**
# ================================
gateway_params = {
    "Name": "Lockon-UG65-70.211",
    "Description": "LoRaWAN Gateway created by Python app and Managed by Autobot",
    "LoRaWAN": {
        "GatewayEui": "24E124FFFEFA3300",  # 网关 EUI
        "RfRegion": "US915"
    },
}

try:
    response = client.create_wireless_gateway(**gateway_params)
    gateway_id = response["Id"]
    print("✅ LoRaWAN 网关创建成功:", json.dumps(response, indent=4))

    # 临时调试使用，暂时不创建了
    # gateway_id = "c5282b3e-5d75-448f-bf5e-c130658bd6e7"

    # 获取网关信息（包括 CUPS 和 LNS）
    gateway_info = client.get_wireless_gateway(
        Identifier=gateway_id,
        IdentifierType='WirelessGatewayId'
    )
    print("ℹ️ 网关信息:", json.dumps(gateway_info, indent=4))

except Exception as e:
    print("❌ 创建网关失败:", str(e))
    exit(-1)



# ================================
# **2. 获取 CUPS/LNS 地址**
# ================================
def save_to_config_file(cups_endpoint, lns_endpoint):
    config = configparser.ConfigParser()

    # 创建 [common] 部分并添加 CUPS 和 LNS 地址
    config['common'] = {
        'CUPS': cups_endpoint,
        'LNS': lns_endpoint
    }
    
    # 检查配置文件是否存在，若存在则备份
    if os.path.exists(config_filename):
        backup_filename = f"aws.ini.bak.{timestamp}"
        try:
            shutil.copy(config_filename, backup_filename)
            print(f"✅ 配置文件已备份: {backup_filename}")
            
            # 删除原始配置文件
            os.remove(config_filename)
            print("✅ 删除原始配置文件成功")
        except Exception as e:
            print(f"❌ 备份或删除配置文件失败: {str(e)}")
            exit(-2)

    # 创建新的配置文件
    try:
        with open(config_filename, "w") as config_file:
            config.write(config_file)
        print(f"✅ 新配置文件已保存: {config_filename}")
    except Exception as e:
        print(f"❌ 保存新配置文件失败: {str(e)}")
        exit(-3)

try:
    cups_response = client.get_service_endpoint(ServiceType="CUPS")
    lns_response = client.get_service_endpoint(ServiceType="LNS")

    CUPS_Endpoint = cups_response["ServiceEndpoint"]
    LNS_Endpoint = lns_response["ServiceEndpoint"]

    cups_id = CUPS_Endpoint.split('.')[0].replace("https://", "")
    lns_id = LNS_Endpoint.split('.')[0].replace("wss://", "")

    print("🔗 CUPS 地址:", CUPS_Endpoint)
    print("🔗 LNS 地址:", LNS_Endpoint)
    print("🆔 CUPS ID:", cups_id)
    print("🆔 LNS ID:", lns_id)
    save_to_config_file(CUPS_Endpoint, LNS_Endpoint)

except Exception as e:
    print("❌ 获取 CUPS/LNS 失败:", str(e))
    exit(-4)

# ================================
# **3. 下载根证书并保存到文件**
# ================================
def download_root_cert(cert_url, cert_filename):
    try:
        # 从 URL 下载根证书
        response = requests.get(cert_url)
        response.raise_for_status()  # 如果请求失败，抛出异常

        # 将证书内容写入文件
        with open(cert_filename, 'w') as cert_file:
            cert_file.write(response.text)
            print(f"✅ 根证书已保存为 {cert_filename}")
    except Exception as e:
        print(f"❌ 下载根证书失败: {str(e)}")
        exit(-5)

# ================================
# **4. 创建证书并关联到网关**
# ================================
def save_certificate_to_files(certificate_pem, private_key, certificate_arn):
    try:
        # 创建时间戳目录
        cert_folder = f"cert-{timestamp}"

        # 创建文件夹
        os.makedirs(cert_folder, exist_ok=True)

        # 根证书下载 URL 和文件名
        root_cert_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        trust_filename = os.path.join(cert_folder, "lns.trust")
        # 下载并保存根证书
        download_root_cert(root_cert_url, trust_filename)

        # 证书文件名称
        cert_filename = os.path.join(cert_folder, f"{certificate_arn.split('/')[-1]}-certificate.pem.crt")
        private_key_filename = os.path.join(cert_folder, f"{certificate_arn.split('/')[-1]}-private.key")

        # 保存 PEM 格式证书
        with open(cert_filename, "w") as cert_file:
            cert_file.write(certificate_pem)
            print(f"✅ 证书已保存为 {cert_filename}")

        # 保存私钥
        with open(private_key_filename, "w") as private_key_file:
            private_key_file.write(private_key)
            print(f"✅ 私钥已保存为 {private_key_filename}")      
    except Exception as e:
        print("❌ 保存证书失败(这怎么可能！！！):", str(e))
        exit(-6)

# 创建证书函数
def create_certificate():
    try:
        cert_response = iot_client.create_keys_and_certificate(
            setAsActive=True
        )
        certificate_arn = cert_response['certificateArn']
        certificate_id = cert_response['certificateId']  # 获取 certificateId
        certificate_pem = cert_response['certificatePem']
        private_key = cert_response['keyPair']['PrivateKey']

        # 保存证书到文件
        save_certificate_to_files(certificate_pem, private_key, certificate_arn)

        # 返回证书 ARN 以供关联
        return certificate_arn  
    except Exception as e:
        print("❌ 创建证书失败（这怎么可能！！！）:", str(e))
        return None

# 关联证书到网关
def attach_certificate_to_gateway(gateway_id, certificate_arn):
    try:
        # 通过 certificateArn 获取 IoT certificateId
        cert_info = iot_client.describe_certificate(certificateId=certificate_arn.split('/')[-1])
        iot_certificate_id = cert_info['certificateDescription']['certificateId']
        
        response = client.associate_wireless_gateway_with_certificate(
            Id=gateway_id,
            IotCertificateId=iot_certificate_id  # 使用 IotCertificateId 进行关联
        )
        print(f"✅ 证书已成功关联到网关: {response}")
    except Exception as e:
        print(f"❌ 关联证书失败: {str(e)}")
        exit(-7)

# 创建证书并关联到网关
certificate_arn = create_certificate()
if certificate_arn:
    attach_certificate_to_gateway(gateway_id, certificate_arn)
