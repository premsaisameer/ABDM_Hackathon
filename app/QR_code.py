from importlib.resources import path
from app import app
from flask import Flask, redirect,send_file,session
import os
from app.sch import gen_SHC

@app.route('/qrcode/<string:abha_id>')
def Qrcode(abha_id):
    path = os.path.abspath(os.path.dirname(__file__))
    # f'{path}/config.yaml'
    img1 = gen_SHC()
    qr_code = f'{abha_id}_QR_code.png'
    img1.save(f'{path}/source/{qr_code}')
    session['k_qr'] = qr_code
    return redirect('/karkinos')

@app.route('/karkinos')
def index():

    path = os.path.abspath(os.path.dirname(__file__))
    qr_code = session['k_qr']
    return send_file(f'{path}/source/{qr_code}')
