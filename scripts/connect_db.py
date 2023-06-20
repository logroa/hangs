import os
from dotenv import load_dotenv

load_dotenv()

DB_USERNAME = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PW') 
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_ENDPOINT = os.getenv('DB_ENDPOINT')

os.system(f'psql postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}')