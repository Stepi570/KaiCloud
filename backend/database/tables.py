
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
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer)
    file_path = Column(String)
    time_send = Column(String)

class Get_file(Base):
    __tablename__ = 'get_file'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer)
    file_path = Column(String)
    time_send = Column(String)
    Sending = Column(String)

class Swap_id_kd(Base):
    __tablename__ = 'swap_id_kd'
    telegram_id = Column(Integer, primary_key=True)
    kd_time = Column(Integer)

class TextMessage(Base):
    __tablename__ = 'text_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer)
    text = Column(String)
    direction = Column(String)  # 'to_telegram' or 'to_site'
    time_send = Column(String)
    is_read = Column(Integer, default=0)
    is_sent = Column(Integer, default=0)  # 0 = не отправлено, 1 = отправлено
    