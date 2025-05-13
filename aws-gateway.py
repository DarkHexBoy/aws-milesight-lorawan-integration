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
# Configure AWS credentials
# ================================
AWS_ACCESS_KEY = "not telling you"
AWS_SECRET_KEY = "not telling you"
REGION = "us-east-1"  # Select the region where AWS IoT Core is located
SERVICE = "iotwireless"
HOST = f"{SERVICE}.{REGION}.amazonaws.com"
ENDPOINT = f"https://{HOST}"

# Initialize AWS clients
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
# **1. Create LoRaWAN Gateway**
# ================================
gateway_params = {
    "Name": "Lockon-UG65-70.211",
    "Description": "LoRaWAN Gateway created by Python app and Managed by Autobot",
    "LoRaWAN": {
        "GatewayEui": "24E124FFFEFA3300",  # Gateway EUI
        "RfRegion": "US915"
    },
}

try:
    response = client.create_wireless_gateway(**gateway_params)
    gateway_id = response["Id"]
    print("✅ LoRaWAN gateway created successfully:", json.dumps(response, indent=4))

    # For temporary debugging, skip creation
    # gateway_id = "c5282b3e-5d75-448f-bf5e-c130658bd6e7"

    # Get gateway information (including CUPS and LNS)
    gateway_info = client.get_wireless_gateway(
        Identifier=gateway_id,
        IdentifierType='WirelessGatewayId'
    )
    print("ℹ️ Gateway information:", json.dumps(gateway_info, indent=4))

except Exception as e:
    print("❌ Failed to create gateway:", str(e))
    exit(-1)


# ================================
# **2. Get CUPS/LNS addresses**
# ================================
def save_to_config_file(cups_endpoint, lns_endpoint):
    config = configparser.ConfigParser()

    # Create [common] section and add CUPS and LNS addresses
    config['common'] = {
        'CUPS': cups_endpoint,
        'LNS': lns_endpoint
    }
    
    # Check if config file exists; if yes, back it up
    if os.path.exists(config_filename):
        backup_filename = f"aws.ini.bak.{timestamp}"
        try:
            shutil.copy(config_filename, backup_filename)
            print(f"✅ Configuration file backed up: {backup_filename}")
            
            # Delete original config file
            os.remove(config_filename)
            print("✅ Original configuration file deleted")
        except Exception as e:
            print(f"❌ Failed to back up or delete config file: {str(e)}")
            exit(-2)

    # Create new config file
    try:
        with open(config_filename, "w") as config_file:
            config.write(config_file)
        print(f"✅ New configuration file saved: {config_filename}")
    except Exception as e:
        print(f"❌ Failed to save new configuration file: {str(e)}")
        exit(-3)

try:
    cups_response = client.get_service_endpoint(ServiceType="CUPS")
    lns_response = client.get_service_endpoint(ServiceType="LNS")

    CUPS_Endpoint = cups_response["ServiceEndpoint"]
    LNS_Endpoint = lns_response["ServiceEndpoint"]

    cups_id = CUPS_Endpoint.split('.')[0].replace("https://", "")
    lns_id = LNS_Endpoint.split('.')[0].replace("wss://", "")

    print("🔗 CUPS Address:", CUPS_Endpoint)
    print("🔗 LNS Address:", LNS_Endpoint)
    print("🆔 CUPS ID:", cups_id)
    print("🆔 LNS ID:", lns_id)
    save_to_config_file(CUPS_Endpoint, LNS_Endpoint)

except Exception as e:
    print("❌ Failed to retrieve CUPS/LNS:", str(e))
    exit(-4)

# ================================
# **3. Download root certificate and save to file**
# ================================
def download_root_cert(cert_url, cert_filename):
    try:
        # Download root certificate from URL
        response = requests.get(cert_url)
        response.raise_for_status()  # Raise exception if request fails

        # Write certificate content to file
        with open(cert_filename, 'w') as cert_file:
            cert_file.write(response.text)
            print(f"✅ Root certificate saved as {cert_filename}")
    except Exception as e:
        print(f"❌ Failed to download root certificate: {str(e)}")
        exit(-5)

# ================================
# **4. Create certificate and attach to gateway**
# ================================
def save_certificate_to_files(certificate_pem, private_key, certificate_arn):
    try:
        # Create timestamped directory
        cert_folder = f"cert-{timestamp}"

        # Create folder
        os.makedirs(cert_folder, exist_ok=True)

        # Root certificate download URL and filename
        root_cert_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        trust_filename = os.path.join(cert_folder, "lns.trust")
        # Download and save root certificate
        download_root_cert(root_cert_url, trust_filename)

        # Certificate file names
        cert_filename = os.path.join(cert_folder, f"{certificate_arn.split('/')[-1]}-certificate.pem.crt")
        private_key_filename = os.path.join(cert_folder, f"{certificate_arn.split('/')[-1]}-private.key")

        # Save PEM certificate
        with open(cert_filename, "w") as cert_file:
            cert_file.write(certificate_pem)
            print(f"✅ Certificate saved as {cert_filename}")

        # Save private key
        with open(private_key_filename, "w") as private_key_file:
            private_key_file.write(private_key)
            print(f"✅ Private key saved as {private_key_filename}")      
    except Exception as e:
        print("❌ Failed to save certificate (how is that even possible!):", str(e))
        exit(-6)

# Function to create certificate
def create_certificate():
    try:
        cert_response = iot_client.create_keys_and_certificate(
            setAsActive=True
        )
        certificate_arn = cert_response['certificateArn']
        certificate_id = cert_response['certificateId']
        certificate_pem = cert_response['certificatePem']
        private_key = cert_response['keyPair']['PrivateKey']

        # Save certificate to files
        save_certificate_to_files(certificate_pem, private_key, certificate_arn)

        # Return certificate ARN for attaching
        return certificate_arn  
    except Exception as e:
        print("❌ Failed to create certificate (how is that even possible!):", str(e))
        return None

# Attach certificate to gateway
def attach_certificate_to_gateway(gateway_id, certificate_arn):
    try:
        # Get IoT certificateId using certificateArn
        cert_info = iot_client.describe_certificate(certificateId=certificate_arn.split('/')[-1])
        iot_certificate_id = cert_info['certificateDescription']['certificateId']
        
        response = client.associate_wireless_gateway_with_certificate(
            Id=gateway_id,
            IotCertificateId=iot_certificate_id  # Use IotCertificateId for association
        )
        print(f"✅ Certificate successfully attached to gateway: {response}")
    except Exception as e:
        print(f"❌ Failed to attach certificate: {str(e)}")
        exit(-7)

# Create certificate and attach it to gateway
certificate_arn = create_certificate()
if certificate_arn:
    attach_certificate_to_gateway(gateway_id, certificate_arn)
