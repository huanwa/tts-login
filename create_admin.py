import os
import boto3
from werkzeug.security import generate_password_hash

# 导入boto3库和werkzeug库的安全模块
# 使用DynamoDB客户端
dynamodb = boto3.resource('dynamodb')
# 使用对应的用户表和管理员表
table_admins = dynamodb.Table('Admins')

# 在你的app模块导入Admin模型

def create_admin(username, password):
    """
    Create an admin user with the provided username and password.
    """
    
    # 生成密码哈希
    hashed_password = generate_password_hash(password)

    # 检查管理员是否已存在
    existing_admin = table_admins.get_item(Key={"username":username}).get('Item')
    if existing_admin:
        print(f'Admin with username {username} already exists.')
        return

    # 在DynamoDB表中创建新的管理员
    table_admins.put_item(
        Item={
            'username': username,
            'password': hashed_password
        }
    )

    print('New admin created successfully.')

if __name__ == '__main__':
    # 使用os.environ获取环境变量
    admin_username = os.environ.get('ADMIN_USERNAME_TTS')
    admin_password = os.environ.get('ADMIN_PASSWORD_TTS')

    if admin_username and admin_password:
        create_admin(admin_username, admin_password)
    else:
        print('Admin username and password must be set as environment variables.')