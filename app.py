from flask import Flask, request, render_template, jsonify, url_for, flash, redirect, session
import boto3
from werkzeug.security import generate_password_hash, check_password_hash
from tts_voice import tts_order_voice
import edge_tts
import anyio
import os, uuid, binascii
import asyncio


language_dict = tts_order_voice

# DynamoDB客户端初始化
dynamodb = boto3.resource('dynamodb')

# DynamoDB 表的引用
table_users = dynamodb.Table('Users')
table_admins = dynamodb.Table('Admins')



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-very-very-secret-key')
# 移除 SQLAlchemy 相关配置
# 其他应用配置保持不变

# 其他全局变量和函数保持不变

# 用户类和用户相关方法修改，移除 SQLAlchemy 模型
class User:
    @staticmethod
    def authenticate(key):
        response = table_users.get_item(
            Key={'key': key}
        )
        return response.get('Item')

# 管理员类和管理员相关方法修改，移除 SQLAlchemy 模型
class Admin:
    @staticmethod
    def authenticate(username, password):
        response = table_admins.get_item(
            Key={'username': username}
        )
        admin = response.get('Item')
        if not admin:
            return '用户不存在'

        if 'password' not in admin:
            return '用户数据不存在密码hash'

        if not check_password_hash(admin['password'], password):
            return '密码错误'  

        return admin

# 移除创建数据库表格的路由，因为 DynamoDB 不需要 pre-create tables in code

# 用户登录
@app.route('/login', methods=['POST'])
def login():
    key = request.form['key']
    user = User.authenticate(key)
    if user:
        session['user_id'] = user['key']
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid key. Please try again.'})



#/admin进入管理员登陆页面
@app.route('/admin', methods=['GET'])
def admin():
    return render_template('generate_key.html')




# 管理员登录路由
@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    admin = Admin.authenticate(username, password)

    print("authenticate result:", admin)

    if isinstance(admin, str):  # 是错误信息
        return jsonify({'success': False, 'message': admin})

    if admin:  # 是 admin 字典
        session['admin_id'] = admin['username']  # 使用字典访问方式
        return jsonify({'success': True})



# 管理员生成新的用户私钥的路由
@app.route('/admin_generate_key', methods=['POST'])
def admin_generate_key():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in as an admin to perform this action'})
    
    # 主要修改这部分逻辑来使用 DynamoDB 来存储数据
    try:
        new_key = binascii.hexlify(os.urandom(24)).decode()
        table_users.put_item(
            Item={
                'key': new_key
                # 如果还有其他字段，也需要在这里添加
            }
        )
        return jsonify({'success': True, 'key': new_key})
    except Exception as e:
        # DynamoDB 推荐的错误处理逻辑
        return jsonify({'success': False, 'message': 'An error occurred: {}'.format(str(e))})



# 使用 asyncio.run 来执行异步函数
def run_asyncio(coroutine):
    return asyncio.run(coroutine)


#用户登录页面路由
@app.route('/', methods=['GET', 'POST'])
def text_to_speech():
    if request.method == 'POST':
        if 'user_id' not in session:
            # 如果用户未登录并且发送了 POST 请求
            return jsonify({'error': 'User not logged in'}), 401
        else:
            # 获取表单数据
            text = request.form.get('text')
            language_code = request.form.get('language_code')
            # 同步调用异步处理函数
            message, filename = run_asyncio(text_to_speech_edge(text, language_code))
            # 获取音频文件的 URL
            audio_url = url_for('static', filename=filename, _external=True)
            # 返回 JSON 响应
            return jsonify({'result_audio_url': audio_url})
    else:
        # GET 请求，渲染首页和选择项
        logged_in = 'user_id' in session
        return render_template('index.html', languages=language_dict.keys(), logged_in=logged_in)
    



# 服务条款页面
@app.route('/tos', methods=['GET']) 
def tos():
    return render_template('terms_of_service.html')




# 异步文本转语音处理函数
async def text_to_speech_edge(text, language_code):
    voice = language_dict[language_code]
    communicate = edge_tts.Communicate(text, voice)
    filename = str(uuid.uuid4()) + ".mp3"
    static_dir = app.static_folder
    tmp_path = os.path.join(static_dir, filename)

    await communicate.save(tmp_path)

    return "语音合成完成：{}".format(text), filename 


# 应用启动
# 逻辑保持不变

if __name__ == "__main__":
    app.run(debug=True)