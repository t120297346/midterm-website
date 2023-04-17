from flask import Flask
from flask import Response, redirect, session
from flask import render_template, url_for, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
# from flask_uploads import patch_request_class
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
from datetime import timedelta, datetime, timezone
from uuid import uuid4
from PIL import Image

class localFlask(Flask):
    def process_response(self, response):
        response.headers['server'] = 'Apache/2.4.38'
        response.headers['x-powered-by'] = 'PHP/5.5.13'
        super(localFlask, self).process_response(response)
        return(response)

app = localFlask(__name__)

app.config['CSRF_SESSION_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOADED_PHOTOS_DEST'] = './upload'
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['UPLOADED_FILES_ALLOW '] = ['jpg', 'png']
app.secret_key = os.urandom(24)

db = SQLAlchemy(app)

photos = UploadSet('photos', tuple('jpg png'.split()))
configure_uploads(app, photos)
# patch_request_class(app) # 限制文件大小

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    password = db.Column(db.String(120))
    uuid = db.Column(db.String(120))
    counter = db.Column(db.Integer)

    def __init__(self, username, password, uuid):
        self.name = username
        self.password = password
        self.uuid = uuid
        self.counter = 1


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    message = db.Column(db.String(120))
    ip = db.Column(db.String(120))
    uuid = db.Column(db.String(120))
    time = db.Column(db.String(120))

    def __init__(self, username, message, ip, uuid, time):
        self.name = username
        self.message = message
        self.ip = ip
        self.uuid = uuid
        self.time = time


class counter(db.Model):
    counter = db.Column(db.Integer, primary_key=True)

    def __init__(self, counter):
        self.counter = 1



@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def page_not_found(e):
    return '<h1>錯了喔😢😢</h1>'



@app.route("/")  # 函式的裝飾
def root():
    return render_template('index.html')


@app.route('/message_board.php', methods=['GET', 'POST'])
def message_board():
    name = session.get('name')

    if name == None:
        return redirect('./login.php')

    if request.method == 'GET':
        user_data = db.session.query(User).filter_by(name=name).first()
        uuid = user_data.uuid
        user_counter = user_data.counter
        user_data.counter += 1

        counter_data = db.session.query(counter).first()
        all_counter = counter_data.counter
        counter_data.counter += 1

        db.session.commit()

        msg = db.session.query(Message).order_by(Message.id)
        return render_template('message_board.html', uuid=uuid, name=name, msg=msg, user_counter=user_counter, all_counter=all_counter,token=generate_csrf())

    elif request.method == 'POST':
        msg = request.values['message']
        if len(msg) > 70:
            return '<h1>會不會太長????<h1>'
        ip = request.remote_addr
        uuid = db.session.query(User).filter_by(name=name).first().uuid
        time = datetime.now() .isoformat()

        new_message = Message(name, msg, ip, uuid, time)
        db.session.add(new_message)
        db.session.commit()
        msg = db.session.query(Message).order_by(Message.id)

        user_data = db.session.query(User).filter_by(name=name).first()
        user_counter = user_data.counter
        user_data.counter += 1

        counter_data = db.session.query(counter).first()
        all_counter = counter_data.counter
        counter_data.counter += 1

        db.session.commit()

        return render_template('message_board.html', name=name, msg=msg, user_counter=user_counter, all_counter=all_counter,token=generate_csrf())


@app.route('/register.php', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print(1)
        name = request.values['name']
        password = request.values['password']
        pwcheck = request.values['pwcheck']
        if len(name) == 0 or len(password) == 0 or len(pwcheck) == 0:
            return '請填好空白處'
        if len(name) > 30:
            return '太多字了  你記不起來'
        elif password != pwcheck:
            return '密碼錯誤😠😠'

        elif '\'' in name:
            rt = '1064 - You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'{}\' at line 1.'.format(name)
            return render_template_string('{{meow}}',meow=rt)

        elif '\'' in password:
            rt = '1064 - You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'{}\' at line 1.'.format(password)
            return render_template_string('{{meow}}',meow=rt)

        elif User.query.filter_by(name=name).count():
            return '重複了  改名喔'
            
        else:
            file_name = request.files['photo'].filename
            sub_file_name = file_name.split('.')[-1]

            uuid = str(uuid4()).replace('-', '')
            filename = photos.save(
                request.files['photo'], name=uuid + '.' + sub_file_name)
            try:
                im = Image.open('./upload/'+filename)
                im = im.resize((100, 100))
                im.save('./upload/'+filename)
            except Exception as e:
                print(e)
                rt = '<h1>Bad 😡😡</h1>'

            # file_url = photos.url(filename)
            new_user = User(name, password, uuid)

            db.session.add(new_user)
            db.session.commit()
            session.clear()
            rt = '註冊成功！ <a href=\"./message_board.php\">留言板</a>'
            return rt


    elif request.method == 'GET':
        return render_template('register.html',token=generate_csrf())


@app.route('/login.php', methods=['GET', 'POST'])
def login():
    rt = ''
    if request.method == 'GET':
        return render_template('/login.html',token=generate_csrf())

    elif request.method == 'POST':
        name = request.values.get('name')
        password = request.values.get('password')
        if len(name) == 0 or len(password) == 0:
            return '不要空白😑😑'
            
        elif '\'' in name:
            rt = '1064 - You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'{}\' at line 1.'.format(name)
            return render_template_string('{{meow}}',meow=rt)

        elif '\'' in password:
            rt = '1064 - You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'{}\' at line 1.'.format(password)
            return render_template_string('{{meow}}',meow=rt)

        elif User.query.filter_by(name=name).count():
            if User.query.filter_by(name=name).first().password == password:
                session['name'] = name
                return redirect('./message_board.php')


@app.route('/delete.php', methods=['POST'])
def delete_message():
    name = session.get('name')
    message_id = request.values.get('id')
    if message_id == None:
        return render_template_string('{{meow}}',meow='要id才能刪啦==')
    else:
        message_obj = Message.query.filter_by(id=message_id).first()
        if message_obj == None:
            return '改ID也沒用喔😀😀'
        elif name != message_obj.name:
            return '不要亂刪🤬🤬'
        else:
            db.session.delete(message_obj)
            db.session.commit()
            return redirect('./message_board.php')


@app.route('/about.php')
def about():
    uid = request.args.get('id')
    name = User.query.filter_by(uuid=uid).first().name
    msg = db.session.query(Message).filter_by(name=name).order_by(Message.id)

    return render_template('about.html', name=name, uid=uid, msg=msg)


@app.route('/logout.php',methods=['POST'])
def logout():
    session['name'] = None
    return redirect('./message_board.php')




if __name__ == "__main__":
    app.debug = True
    CSRFProtect(app)
    app.run("0.0.0.0")