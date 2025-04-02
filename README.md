# aws-milesight-lorawan-integration
deepseek + kimi + chatgpt 联合开发

主要功能：
1. UG65 以 basic station 的方式连接 AWS 的 Iot Core 平台
2. 创建 sensor 的预配置参数：主要包含：创建 IAM Role 角色，创建 Lambda 函数（内含自动生成的 Decode 代码），配置 Lambda 的 trigger，创建 Rule
3. 添加 sensor ，这里以 AM308 作为案例进行开发，整体流程：创建 device profile，创建 service profile，添加 lorawan 设备，创建 destination （ RULE_NAME 需要从预配置参数那边获取 ）
4. 所有代码目前比较粗糙，仅供参考


非 Administrator 用户的情况下需要的权限，参考 permission.txt 文档。
