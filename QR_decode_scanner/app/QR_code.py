import json
from flask import request
from app.sch_decode import QRdecode , verification
from app import app

@app.route('/decode', methods= ['POST'])
def decodeQR():
    json_args = json.loads(request.data)
    qr_data = json_args['qr_data']
    fhir_bundle = QRdecode(qr_data)
    return fhir_bundle


@app.route('/verification', methods= ['POST'])
def verify():
    json_args = json.loads(request.data)
    qr_data = json_args['qr_data']
    Verification_status = verification(qr_data)
    return Verification_status

  