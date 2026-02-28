from datetime import datetime
from database.config import get_db_session
from database.tables import Requests,Sending
from database.random import random_string

class DBRequests():
    def __init__(self):
        self.session = get_db_session()

    def new_human(self,telegram_id):
        with self.session() as session:
            site_id_user = session.query(Requests.site_id).filter(Requests.telegram_id == telegram_id).first()
            if site_id_user:
                update_user = session.query(Requests).filter(Requests.site_id == site_id_user[0]).first()
                update_user.time_finish = datetime.now().timestamp() + 600
                session.commit()
                return update_user.site_id
            else:   
                site_ids_user = session.query(Requests.site_id).all()
                random_string_id = random_string(site_ids_user)
                new_user = Requests(site_id=random_string_id,telegram_id=telegram_id, time_finish=datetime.now().timestamp() + 600)
                session.add(new_user)
                session.commit()
                return random_string_id
            
    
    def all_site_id(self):
        with self.session() as session:
            site_id = session.query(Requests.site_id).all()
            return site_id

    def check_id(self, site_id):
        with self.session() as session:
            user = session.query(Requests).filter(Requests.site_id == site_id).first()
        if user and user.time_finish > datetime.now().timestamp():
            return user.telegram_id
        return False
    
    def check_time_from_telegram_id(self, telegram_id):
        with self.session() as session:
            user = session.query(Requests).filter(Requests.telegram_id == telegram_id).first()
        if user and user.time_finish > datetime.now().timestamp():
            return True
        return False
    
    def new_file(self, telegram_id, file_name):
        with self.session() as session:
            user = Sending()