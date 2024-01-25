# import boto3

# session = boto3.session.Session()
# credentials = session.get_credentials()
# current_credentials = credentials.get_frozen_credentials()
# print(current_credentials)








import boto3

# 创建S3客户端
s3 = boto3.client('s3')

# 尝试列出S3存储桶中的对象
try:
    response = s3.list_objects_v2(Bucket='tts-wh')
    print("Successful connection!")
except Exception as e:
    print("Failed to connect: ", e)


#print(boto3.client('sts').get_caller_identity().get('Account'))