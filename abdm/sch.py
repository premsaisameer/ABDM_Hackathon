''' Script for generating/issuing SMART health cards. '''

import chunk
import json
import zlib
import sys
import qrcode
import yaml
from jwcrypto import jwk, jws
from jwcrypto.common import json_encode
from pprint import pprint
from math import ceil
# from textwrap3 import wrap
import os

# Utils =============================================================
# (for compressing/decompressing the payload)

def deflate(string_val):
    ''' Take a str, compress and url-safe b64 encode it.'''
    zlibbed_str = zlib.compress(string_val.encode())
    compressed_string = zlibbed_str[2:-4] # omit zlib headers, per spec
    return compressed_string

def inflate( compressed ):
    ''' Take compressed bytes, convert to original str.'''
    return zlib.decompress(compressed, -15).decode("utf-8")

# Main token-creation functions =========================================

def get_FHIR_bundle1(conf):
    ''' Generate the vaccination record itself.'''

    given_names = conf["given_names"]
    if type(given_names) == str:
        given_names = given_names.split(" ")

    patient = {
      'fullUrl': 'resource:0', 
      'resource': {
        'resourceType': 'Patient', 
        'name': [{'family': conf['family_name'], 'given': given_names}], 
        'birthDate': str(conf['date_of_birth'])}
    }

    imm1 = { 'fullUrl': 'resource:1', 
      'resource': {
            'resourceType': 'Immunization', 
            'status': 'completed', 
            'vaccineCode': {'coding': [{'system': 'http://hl7.org/fhir/sid/cvx', 'code': '207'}]}, 
            'patient': {'reference': 'resource:0'},
            'occurrenceDateTime': str(conf['first_shot']['date']), 
            'performer': [{'actor': 
                {'display': conf['first_shot']['administered_by']}}],
            'lotNumber': str(conf['first_shot']['lot_number'])
      }
    }

    imm2 = {
      'fullUrl': 'resource:2', 
      'resource': {
        'resourceType': 'Immunization',
        'status': 'completed',
        'vaccineCode': {'coding': [{'system': 'http://hl7.org/fhir/sid/cvx', 'code': '207'}]}, 
        'patient': {'reference': 'resource:0'}, 
        'occurrenceDateTime': str(conf['second_shot']['date']), 
        'performer': [{'actor': 
            {'display': conf['second_shot']['administered_by']}}], 
            'lotNumber': conf['second_shot']['lot_number']
      }
    }

    FHIR = {
        "resourceType":"Bundle",
        "type":"collection",
        "entry": [patient,imm1,imm2]
    }

    FHIR = json.load(open('bundle.json', 'r'))
    return FHIR

def get_FHIR_bundle(conf):
    # FHIR = json.load(open('PatientObservation.json', 'r'))
    FHIR = json.load(open('bundle.json', 'r'))
    return FHIR

def get_VC_bundle(FHIR, issuer_url):
    ''' Given FHIR bundle, generate VerifiableCredential bundle. '''

    vc = {
        "iss":issuer_url,
        "nbf":0, # "Not before" (in seconds since epoch, TODO set 2 weeks after 2nd vaccination)
        "vc": {
            "type":[
                "https://smarthealth.cards#health-card",
                "https://smarthealth.cards#immunization",
                "https://smarthealth.cards#covid-19",
            ],
            "credentialSubject":{
                "fhirVersion":"4.0.1",
                "fhirBundle":FHIR
            }
        }
    }

    return vc

def make_chunk(token):
    token_size = len(token)
    number_of_chunk = ceil(token_size/1191)
    chunk_size = token_size // number_of_chunk

    chunks = []
    for i in range(number_of_chunk):
        if i+1 == number_of_chunk:
            chunks.append(token[chunk_size*i : ])
        else:
            chunks.append(token[chunk_size*i : (i+1)*chunk_size])

    return chunks, number_of_chunk


def token_to_qr(token, i, number_of_chunk):
    ''' Implement the weird numerical encoding used by the shc standard. '''
    print('=======================',len(token))
    print(token)
    qr = f"shc:/{i}/{number_of_chunk}/" + "".join([f"{(ord(c)-45):02d}" for c in token])
    return qr

# Crypto stuff ======================================================

def gen_keys():
    ''' Generates public/private key pair.  Writes two files:
      jwks.json: public key, to be placed at issuer_url/.well-known/jwks.json
      private_jwk.json: jwk file for private key, to be kept secret.
    '''
    key = jwk.JWK.generate(**{"kty":"EC", "crv":"P-256", "alg":"ES256", "use":"sig"})
    key_info = json.loads(key.export(private_key=True))

    print(key.export(private_key=True))
    
    key_info["kid"] = key.thumbprint()

    with open("private_jwk.json","w") as f:
        json.dump(key_info, f)

    del key_info["d"] # Very Important! Don't make private key public.

    with open("jwks.json","w") as f:
        obj = {"keys":[key_info]}
        json.dump(obj,f)

def sign_JWS(payload, key_file="private_jwk.json"):
    ''' Given a payload (already compressed/encoded) and a json file
    representing the private key information, sign and encode into a
    serialized jws token.'''

    key_data = json.load(open(key_file, "r"))
    private_key = jwk.JWK(**key_data)

    header = {"kid":private_key.thumbprint(), "zip":"DEF", "alg":"ES256"}

    token = jws.JWS(payload)
    token.add_signature(private_key, alg="ES256", protected=json_encode(header))

    return token.serialize(compact=True) # b64 string of the token.

def load_and_verify_jws_token(token, key_file="example_jwks.json"):
    ''' Read & validate a serialized token.
    
    Throws an error if invalid (assuming signed by the example issuer),
    otherwise returns the (decompressed) payload (in dict form).
    
    Lots of hacks in this, since I just used it for testing.  This is not
    good as a general-purpose smart-health-card file reader.'''

    # Load public key from file.
    # TODO Fetch from specified url?
    #  (This would require extracting the package without verifying, which this
    #  jws library does not allow...)
    with open(key_file,"r") as f:
        key_data = json.load(f)

    # TODO Check correct key, not just the first one.
    public_key = jwk.JWK(**key_data["keys"][0])

    jws_token = jws.JWS()
    jws_token.deserialize(token)
    jws_token.verify(public_key)

    return json.loads(inflate(jws_token.payload)) # inflate = uncompress

def remove_files(f):
    try:
        for element in os.listdir(f):
            os.remove(os.path.join(f, element))
    except:
        pass
# Main ===================================================================

def gen_SHC(config_file="config.yaml", write_file=False):
    ''' Generate a smart health card based on the given config file.'''
    config = yaml.load(open(config_file, "r"), Loader=yaml.FullLoader)

    issuer_url = config['issuer_url']
    key_file = config['key_file']
    output_file = config['output_file']

    FHIR = get_FHIR_bundle(config)
    vc = get_VC_bundle(FHIR, issuer_url=issuer_url)

    payload = deflate(json.dumps(vc, separators=(",", ":")))

    jws_token = sign_JWS(payload, key_file=key_file) # NB: is str, not bytes
    print('======================================')
    print(type(jws_token))
    print(jws_token)

    # Write smart health file
    if write_file:
        final_data = json.dumps({"verifiableCredential": [jws_token]})
        with open("test.smart-health-card","w") as f:
            f.write(final_data)
        
    # Generate QR code.
    chunks, number_of_chunk = make_chunk(jws_token)

    os.makedirs('qr_code', exist_ok=True)
    remove_files('qr_code')

    for i, chunk in enumerate(chunks, 1):
        img = qrcode.make(token_to_qr(chunk, i, number_of_chunk))
        print(type(img))
        return img
        # img.save(f'qr_code/chunk_{i}.png')

print('========================================================')
if __name__=="__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  To generate public/private key pair:")
        print("    python shc.py gen_keys\n")
        print("  To generate qr code: ")
        print("    python shc.py <config.yaml>")
        sys.exit(1)

    if sys.argv[1] == "gen_keys":
        gen_keys()
        sys.exit(1)
    else:
        gen_SHC(sys.argv[1])
        sys.exit(1)