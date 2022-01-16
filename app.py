#!/usr/bin/env python3
# -*- conding: utf-8 -*-

import os
import cv2
import uuid
import numpy as np
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, make_response

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './upload/'
# 限制上传文件的大小（4Mb）
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
# 限制上传文件类型
ALLOWED_EXTENSIONS = set(['jpg', 'png'])

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/signin', methods=['GET'])
def signin_form():
    return render_template('signin.html')

@app.route('/signin', methods=['POST'])
def sigin():
    username = request.form['username']
    password = request.form['password']
    # 从 request 表单获取数据
    if username == 'admin' and password == 'admin123':
        return render_template('signin-ok.html', username=username)
    return render_template('signin.html', message='Bad username or password.', username=username)

@app.route('/html2canvas', methods=['GET'])
def html2canvas():
    return render_template('html2canvas.html')

@app.route('/qrcode', methods=['GET'])
def qrcode():
    return render_template('qrcode.html')

@app.route('/upload', methods=['GET'])
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['picter']
    filename = random_filename(secure_filename(f.filename))

    # 保存图片
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # 加载图片
    input_filename = app.config['UPLOAD_FOLDER'] + filename
    output_dir = './static/'
    output_filename = output_dir + filename
    img = cv2.imread(input_filename, cv2.IMREAD_COLOR)

    ## 1. 转换为灰度和阈值
    ## (1) Convert to gray, and threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    th, threshed = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    ## 2. Morph-op 去除噪音
    ## (2) Morph-op to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
    morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

    ## 3. 找到最大面积轮廓
    ## (3) Find the max-area contour
    cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    cnt = sorted(cnts, key=cv2.contourArea)[-1]

    ## 4. 裁剪并保存
    ## (4) Crop and save it
    x,y,w,h = cv2.boundingRect(cnt)
    dst = img[y:y+h, x:x+w]

    # 提取图片中的红色区域
    hsv = cv2.cvtColor(dst, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0,70,50])
    upper_red = np.array([10,255,255])
    mask1 = cv2.inRange(hsv, lower_red, upper_red)
    lower_red = np.array([170,70,50])
    upper_red = np.array([180,255,255])
    mask2 = cv2.inRange(hsv, lower_red, upper_red)
    mask = cv2.add(mask1, mask2)

    # 背景透明
    # output_img = mask.copy()
    # output_img[np.where(mask==0)] = 0
    output_hsv = dst.copy()
    output_hsv = cv2.cvtColor(output_hsv, cv2.COLOR_BGR2BGRA)
    output_hsv[np.where(mask==0)] = [255,255,255,0]
    cv2.imwrite(output_filename, output_hsv)

    image_data = open(os.path.join(output_dir, '%s' % filename), "rb").read()
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/png'
    return response

def random_filename(filename):
    ext = os.path.splitext(filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=8086)