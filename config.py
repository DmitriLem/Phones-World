import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_super_secret_key_1234567890NobodyWillGetThisKeyAnyway')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'userUploadPhotos')
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    API_TOKEN = os.getenv('API_TOKEN', '86c960f33f9c64')
    
    #MSSQL
    DB_SERVER = os.getenv('DB_SERVER', 'dbinventory.cz84gqqau37j.us-east-2.rds.amazonaws.com')
    DB_DATABASE = os.getenv('DB_DATABASE', 'Inventory')
    DB_USERNAME = os.getenv('DB_USERNAME', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'NtFqQ4Ap')
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

    #Email
    EMAIL_CFG = {
        'sender_email': os.getenv('SENDER_EMAIL', 'YamiWrk@outlook.com'),
        'sender_password': os.getenv('SENDER_PASSWORD', 'q@jau89pvgw#/Qx'),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587))
    }