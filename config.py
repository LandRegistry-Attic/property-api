import os


class Config(object):
    DEBUG = False
    PPI_END_POINT = os.environ['PPI_END_POINT']
    SQLALCHEMY_DATABASE_URI = os.environ['POSTGRES_DATABASE_URI'] 


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(DevelopmentConfig):
    TESTING = True
