import logging
from flask import Flask
from logging import config
import requests
import json

from config import CONFIG_DICT

app = Flask(__name__)
app.config.update(CONFIG_DICT)


def setup_logging():
    logging_config_file_path = app.config['LOGGING_CONFIG_FILE']

    try:
        with open(logging_config_file_path, 'rt') as file:
            config = json.load(file)
        logging.config.dictConfig(config)
    except IOError as e:
        raise(Exception('Failed to load logging configuration', e))

setup_logging()

