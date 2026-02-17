import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_CONNECTION = create_engine(f"postgresql+psycopg2://postgres:0501Valeev@postgres:5432/kaicloud")

SECRET_KEY = "fl3GT6vQJg+eBxO+qOnCVVUSgf7u5vo3zCRaoGO+1h4="

Session = sessionmaker(DATABASE_CONNECTION)

def get_db_session():
    return Session