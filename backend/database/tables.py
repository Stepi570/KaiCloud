
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Requests(Base):
    __tablename__ = 'requests'
    site_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    time_finish = Column(Integer)

class Sending(Base):
    __tablename__ = 'sending'
    telegram_id = Column(Integer, primary_key=True)
    file_path = Column(String)
    time_send = Column(Integer)
    