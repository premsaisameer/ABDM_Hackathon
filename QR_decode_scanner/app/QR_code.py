from flask import Flask, redirect, request, jsonify, send_file,session
import os,json
from app.sch_decode import QRdecode 
from app import app


@app.route('/decode', methods= ['POST'])
def decodeQR():
    path = os.path.abspath(os.path.dirname(__file__))
    # file = request.files['image']
    fhir_bundle = QRdecode(path)
    return fhir_bundle