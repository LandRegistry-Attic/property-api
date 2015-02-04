import os, logging
from flask import Flask
import requests

app = Flask(__name__)

app.config.from_object(os.environ.get('SETTINGS'))
