### **AWS Milesight LoRaWAN Integration**   

## **主要功能**  
1. **UG65 连接 AWS IoT Core**  
   - 采用 **Basic Station** 模式将 UG65 连接到 AWS IoT Core 平台。  

2. **Sensor 预配置参数**  
   - 创建 **IAM Role** 角色。  
   - 创建 **Lambda 函数**（内含自动生成的 Decode 代码）。  
   - 配置 **Lambda 的触发器（Trigger）**。  
   - 创建 **Rule** 规则。  

3. **添加 Sensor（以 AM308 为案例）**  
   - 创建 **Device Profile**。  
   - 创建 **Service Profile**。  
   - 添加 **LoRaWAN 设备**。  
   - 创建 **Destination**（`RULE_NAME` 需要从预配置参数获取）。  

4. **当前代码状态**  
   - 所有代码目前仍较为初步，仅供参考。  

## **权限要求**  
对于 **非 Administrator 用户**，请参考 `permission.txt` 文档，确保拥有必要的权限。  

## **环境要求**  
- Python **3.8.20**  

## **依赖包**  
以下为 `requirements.txt` 依赖列表：  
```txt
aws-requests-auth==0.4.3
boto3==1.37.20
botocore==1.37.20
certifi==2025.1.31
charset-normalizer==3.4.1
idna==3.10
jmespath==1.0.1
python-dateutil==2.9.0.post0
requests==2.32.3
s3transfer==0.11.4
six==1.17.0
urllib3==1.26.20
```
## **安装依赖**  
建议使用以下命令安装依赖：  
```sh
pip install -r requirements.txt
```
