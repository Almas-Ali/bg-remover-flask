from flask import Flask, render_template, request, redirect, url_for
from peewee import *
from datetime import datetime as dt
import string
import random
import os
from rembg import remove
from PIL import Image


db = SqliteDatabase('sqlite.db')


class BaseModel(Model):
    class Meta:
        database = db


class Photos(BaseModel):
    name = CharField()
    path = CharField()
    ip = CharField()
    date = DateTimeField(default=dt.now())


db.connect()
db.create_tables([Photos], safe=True)


def unique_name(name: str):
    name = name.replace(' ', '_')
    name = name.replace('-', '_')
    random_str = string.ascii_letters+string.digits
    random_api = random.sample(random_str, 20)
    random_api = ''.join(random_api)
    return f"{random_api}_{name}"


def get_client_ip():
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)


def remove_bg(input_path, output_path):
    input = Image.open(input_path)
    output = remove(input)

    output_path = output_path.split('.')
    output_path[1] = 'png'
    output_path = '.'.join(output_path)
    
    output.save(output_path)

    return output_path


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/media')
app.config['ALLOWED_EXTENSIONS'] = ['jpg', 'png']
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 2  # 2mb


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        photo_name = unique_name(file.filename)
        file.save(dst=os.path.join(app.config['UPLOAD_FOLDER'], photo_name))

        photo = Photos(name=photo_name,
                       path=f"media/{photo_name}", ip=get_client_ip())
        photo.save()
        
        removed_file = remove_bg(os.path.join(app.config['UPLOAD_FOLDER'], photo_name), 'static/media/'+photo_name)
        removed_file = removed_file.replace('static/', '')
        return render_template('editor.html', photo=removed_file)

    return redirect('/')


@app.route('/photos')
def photos():
    photos = Photos.select().order_by(Photos.date.desc()).dicts()
    return render_template('photos.html', photos=photos)


if __name__ == '__main__':
    app.run(debug=True)
