# **AWS Milesight LoRaWAN Integration**

## **Main Features**
1. **UG65 Connection to AWS IoT Core**  
   - Connect UG65 to AWS IoT Core platform using **Basic Station** mode.

2. **Sensor Pre-configuration Parameters**  
   - Create an **IAM Role**.  
   - Create a **Lambda function** (includes auto-generated decoding code).  
   - Configure the **Lambda trigger**.  
   - Create a **Rule**.

3. **Add Sensor (Using AM308 as an Example)**  
   - Create a **Device Profile**.  
   - Create a **Service Profile**.  
   - Add a **LoRaWAN device**.  
   - Create a **Destination** (`RULE_NAME` should be obtained from the pre-configuration parameters).

4. **Current Code Status**  
   - All code is currently in an early stage and for reference only.

## **Permission Requirements**
For **non-Administrator users**, please refer to the `permission.txt` file to ensure the necessary permissions are granted.

## **Environment Requirements**
- Python **3.8.20**

## **Dependencies**
Below is the list from `requirements.txt`:

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
## **Install Dependencies**  
It is recommended to install dependencies using the following command:  
```sh
pip install -r requirements.txt
```

