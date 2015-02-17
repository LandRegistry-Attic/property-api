import os


class Config(object):
    DEBUG = False
    PPI_END_POINT = os.environ['PPI_END_POINT']
    ELASTIC_SEARCH_ENDPOINT = os.environ['ELASTIC_SEARCH_ENDPOINT']


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(DevelopmentConfig):
    TESTING = True
