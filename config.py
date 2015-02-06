import os


class Config(object):
    DEBUG = False
    PPI_END_POINT = os.environ['PPI_END_POINT']
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:seekritpwd@172.16.42.43:5432/pubdata'


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(DevelopmentConfig):
    TESTING = True
