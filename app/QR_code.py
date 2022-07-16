from importlib.resources import path
from app import app
from flask import Flask,send_file
import os


@app.route('/karkinos')
def index():
    path = os.path.abspath(os.path.dirname(__file__))
    print("Path",os.path.abspath(os.path.dirname(__file__)))
    return send_file(f'{path}/source/output.png',as_attachment=True)
