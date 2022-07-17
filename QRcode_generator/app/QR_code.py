from importlib.resources import path
from app import app
from flask import Flask, redirect,send_file,session,request
import os,json
from app.sch import gen_SHC

@app.route('/qrcode/<string:abha>',methods = ['POST'])
def Qrcode(abha):
    path = os.path.abspath(os.path.dirname(__file__))
    # json_data = json.loads(request.data)
    
    # abha = json_data['abha']
    # # f'{path}/config.yaml'
    img1 = gen_SHC()
    qr_code = f'{abha}_QR_code.png'
    img1.save(f'{path}/source/{qr_code}')
    return send_file(f'{path}/source/{qr_code}',as_attachment=True)
    # session['k_qr'] = qr_code
    
# return redirect('/karkinos')
 
# @app.route('/karkinos')
# def index():

#     path = os.path.abspath(os.path.dirname(__file__))
#     qr_code = session['k_qr']
#return send_file(f'{path}/source/{qr_code}',as_attachment=True)
