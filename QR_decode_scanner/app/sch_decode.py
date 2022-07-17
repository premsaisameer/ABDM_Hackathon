import zlib
import qrcode
import cv2
import re
import base64
import json
from pprint import pprint
import os
from pyzbar.pyzbar import decode as dec
from jwcrypto import jwk, jws
from jwcrypto.common import json_encode

# ================================================
def load_and_verify_jws_token(token, key_file="jwks.json"):
    ''' Read & validate a serialized token.
    
    Throws an error if invalid (assuming signed by the example issuer),
    otherwise returns the (decompressed) payload (in dict form).
    
    Lots of hacks in this, since I just used it for testing.  This is not
    good as a general-purpose smart-health-card file reader.'''

    # Load public key from file.
    # TODO Fetch from specified url?
    #  (This would require extracting the package without verifying, which this jws library does not allow...)
    
    path = os.path.abspath(os.path.dirname(__file__))
    with open(f"{path}/{key_file}", "r") as f:
        key_data = json.load(f)

    # TODO Check correct key, not just the first one.
    public_key = jwk.JWK(**key_data["keys"][0])

    jws_token = jws.JWS()
    jws_token.deserialize(token)
    jws_token.verify(public_key)

    return json.loads(inflate(jws_token.payload)) # inflate = uncompress
# =======================================================

def get_qr_code_image1(qr_code):
    img = cv2.imread(qr_code)
    det = cv2.QRCodeDetector()
    return det.detectAndDecode(img)

def get_qr_code_image(qr_code):
    image = cv2.imread(qr_code)
    barcodes = dec(image)
    val = barcodes[0].data.decode('utf-8')
    return val

def qr_to_token1(qr_data):
    parts = re.findall('..', qr_data[9:])
    jws = ""
    for p in parts:
        jws += chr(int(p)+ 45)
    return jws

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

def decode(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += 'b'* (4 - missing_padding)
        return base64.urlsafe_b64decode(data)

def inflate(jws_parts):
    shc_data = zlib.decompress(jws_parts, wbits=-15).decode("utf-8") # {"iss":"https://c19.cards/issuer","nbf":1591037940,"vc":{"type":["https://smarthealth.cards#covid19", ...
    return shc_data

def inflate_(jws_parts):
    shc_data = zlib.decompress(jws_parts[1], wbits=-15).decode("utf-8") # {"iss":"https://c19.cards/issuer","nbf":1591037940,"vc":{"type":["https://smarthealth.cards#covid19", ...
    return shc_data

def get_FHIR_bundle(shc_data):
    shc_data = json.loads(shc_data)
    return shc_data['vc']['credentialSubject']['fhirBundle']


def QRdecode(path):
    qr_file = os.listdir(f'{path}/source')
    # qr_file = ['chunk_1.png']
    jws = ""
    for file in qr_file:
        # val, pts, st_code = get_qr_code_image1(f"qr_code/{file}")
        val = get_qr_code_image(f'{path}/source/{file}')

        jws += qr_to_token(val)
    
    jws_parts = list(map(decode, jws.split(".")))
    
    # tmp = json.loads(jws).decode('utf-8')
    # abc = load_and_verify_jws_token(jws)

    shc_data = inflate_(jws_parts)
    fhir = get_FHIR_bundle(shc_data)
    return fhir