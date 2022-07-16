from flask import Flask,send_file
app = Flask("app")

app.secret_key = 'Karkinos'
from app import QR_code

