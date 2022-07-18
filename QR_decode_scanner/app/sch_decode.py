import zlib
import re
import base64
import json
import os
from jwcrypto import jwk, jws


# ================================================
def load_and_verify_jws_token(token, key_file="jwks.json"):
    
    path = os.path.abspath(os.path.dirname(__file__))
    with open(f"{path}/{key_file}", "r") as f:
        key_data = json.load(f)
    try: 
        # TODO Check correct key, not just the first one.
        public_key = jwk.JWK(**key_data["keys"][0])

        jws_token = jws.JWS()
        jws_token.deserialize(token)
        jws_token.verify(public_key)
        return "Verification Successful"
    except:
        return "Verification failed"
    # inflate = uncompress
# =======================================================
def qr_to_token(qr_data):
    li = qr_data.split('/')
    chunk_number = li[1]
    total_chunk = li[2]
    data = "".join(li[3:])

    parts = re.findall('..', data)

    jws = ""
    for p in parts:
        jws += chr(int(p)+ 45)
    return jws

# =======================================================
def decode(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += 'b'* (4 - missing_padding)
        return base64.urlsafe_b64decode(data)

# =======================================================
def inflate_(jws_parts):
    shc_data = zlib.decompress(jws_parts[1], wbits=-15).decode("utf-8") # {"iss":"https://c19.cards/issuer","nbf":1591037940,"vc":{"type":["https://smarthealth.cards#covid19", ...
    return shc_data

# =======================================================
def get_FHIR_bundle(shc_data):
    shc_data = json.loads(shc_data)
    return shc_data['vc']['credentialSubject']['fhirBundle']

# =======================================================
def QRdecode(qr_data):
    jws_ = ""
    jws_ += qr_to_token(qr_data)
    jws_parts = list(map(decode, jws_.split(".")))
    shc_data = inflate_(jws_parts)
    fhir = get_FHIR_bundle(shc_data)
    return processed_fhir_bundle(fhir)

# =======================================================
def processed_fhir_bundle(fhir_bundle):
    processed_bundle = {}
    processed_bundle['patients'] = {}

    patient = processed_bundle['patients']
    patient['Demographics'] = {}
    patient['clinicalData'] = {}
    patient['clinicalData']['FamilyHistory'] = []
    patient['clinicalData']['Procedures'] =[]
    patient['clinicalData']['Allergies'] =[]
    patient['clinicalData']['Medication'] =[]

    try :   
        patient['meta'] = fhir_bundle['meta']
    except:
        pass
    for x in fhir_bundle['entry']:
        print(x['resource']['resourceType'])
        if x['resource']['resourceType'] == 'Patient':
            patient['patientID'] = x['resource']['identifier'][0]['value']
            patient['Demographics']['name'] = x['resource']['name'][0]['text']
            patient['Demographics']['gender'] = x['resource']['gender']
            patient['Demographics']['birthDate'] = x['resource']['birthDate']
        elif x['resource']['resourceType'] == 'FamilyMemberHistory':
            val = {}
            val['display']=(x['resource']['condition'][0]['code']['coding'][0]['display'])
            patient['clinicalData']['FamilyHistory'].append(val)
        elif x['resource']['resourceType'] == 'Procedure':
            val = {}
            val['display']=(x['resource']['code']['coding'][0]['display'])
            patient['clinicalData']['Procedures'].append(val)
        elif x['resource']['resourceType'] == 'MedicationStatement':
            val = {}
            val['display']=(x['resource']['medicationCodeableConcept']['coding'][0]['display'])
            patient['clinicalData']['Medication'].append(val)

    return processed_bundle

# =======================================================
def verification(qr_data):
    jws_ = ""
    jws_ += qr_to_token(qr_data)    
    return(load_and_verify_jws_token(jws_))