import os


class Config(object):
    DEBUG = False
    PPI_END_POINT = os.environ['PPI_END_POINT']
    ELASTIC_SEARCH_ENDPOINT = os.environ['ELASTIC_SEARCH_ENDPOINT']
    LOGGING_CONFIG_FILE = os.environ['LOGGING_CONFIG_FILE']


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(DevelopmentConfig):
    TESTING = True
