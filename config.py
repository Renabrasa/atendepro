import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-segura'

    # String de conexão para MySQL no AWS RDS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://admin:At241286@atendepro.cep6qq66kx3j.us-east-1.rds.amazonaws.com:3306/atendepro'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
