from importlib.resources import path
from app import app
from flask import Flask, redirect,send_file,session,request
import os,json
from app.sch import gen_SHC

@app.route('/qrcode/<string:abha>',methods = ['POST'])
def Qrcode(abha):
    path = os.path.abspath(os.path.dirname(__file__))
    img1 = gen_SHC()
    qr_code = f'{abha}_QR_code.png'
    img1.save(f'{path}/source/{qr_code}')
    return send_file(f'{path}/source/{qr_code}',as_attachment=True)
   