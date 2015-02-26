import os

CONFIG_DICT = {
    'DEBUG': False,
    'PPI_END_POINT': os.environ['PPI_END_POINT'],
    'ELASTIC_SEARCH_ENDPOINT': os.environ['ELASTIC_SEARCH_ENDPOINT'],
    'LOGGING_CONFIG_FILE': os.environ['LOGGING_CONFIG_FILE'],
}

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
