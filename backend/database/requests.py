from datetime import datetime, timedelta
from database.config import get_db_session
from database.tables import Get_file, Requests,Sending, Swap_id_kd, TextMessage
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
    
    def new_file(self, telegram_id, file_path):
        with self.session() as session:
            print(file_path)
            user = Sending(telegram_id=telegram_id, file_path=str(file_path), time_send=(datetime.now() + timedelta(hours=3)).strftime("%H:%M %d.%m.%Y"))
            session.add(user)
            session.commit()

    def check_sending_file(self, telegram_id):
        with self.session() as session:
            user = session.query(Get_file).filter(Get_file.telegram_id == telegram_id, Get_file.Sending == "sending").first()
        if user:
            return True
        return False
    
    def new_sending(self, telegram_id, file_path):
        with self.session() as session:
            user = Get_file(telegram_id=telegram_id, file_path=str(file_path), time_send=(datetime.now() + timedelta(hours=3)).strftime("%H:%M %d.%m.%Y"), Sending="sending")
            session.add(user)
            session.commit()

    def swap_sending(self, telegram_id, status):
        with self.session() as session:
            user = session.query(Get_file).filter(Get_file.telegram_id == telegram_id).order_by(Get_file.id.desc()).first()
            user.Sending = status
            session.commit()

    def swap_person_id(self, telegram_id) -> int:
        with self.session() as session:
            site_ids_user = session.query(Requests.site_id).all()
            random_string_id = random_string(site_ids_user)
            user = session.query(Requests).filter(Requests.telegram_id == telegram_id).first()
            user.site_id = random_string_id
            session.commit()
            user = session.query(Swap_id_kd).filter(Swap_id_kd.telegram_id == telegram_id).first()
            if not user:
                new_user = Swap_id_kd(telegram_id=telegram_id, kd_time=datetime.now().timestamp() + 3600)
                session.add(new_user)
            else:
                user.kd_time = datetime.now().timestamp() + 3600
            session.commit()
            return random_string_id
    
    def chek_swap_id_kd(self, telegram_id) -> bool:
        with self.session() as session:
            user = session.query(Swap_id_kd).filter(Swap_id_kd.telegram_id == telegram_id).first()

        if user == None or user.kd_time < datetime.now().timestamp():
            return False
        return True
    
    def close_cloud(self, telegram_id):
        with self.session() as session:
            user = session.query(Requests).filter(Requests.telegram_id == telegram_id).first()
            if user:
                user.time_finish = datetime.now().timestamp()
                session.commit()
                return True
    
    # Методы для текстовых сообщений
    def save_text_message(self, telegram_id, text, direction):
        with self.session() as session:
            message = TextMessage(
                telegram_id=telegram_id,
                text=text,
                direction=direction,
                time_send=(datetime.now() + timedelta(hours=3)).strftime("%H:%M %d.%m.%Y"),
                is_read=0,
                is_sent=0
            )
            session.add(message)
            session.commit()
            return message.id
    
    def get_text_messages(self, telegram_id, direction=None):
        with self.session() as session:
            if direction:
                messages = session.query(TextMessage).filter(
                    TextMessage.telegram_id == telegram_id,
                    TextMessage.direction == direction
                ).order_by(TextMessage.id.desc()).all()
            else:
                messages = session.query(TextMessage).filter(
                    TextMessage.telegram_id == telegram_id
                ).order_by(TextMessage.id.desc()).all()
            return messages
    
    def get_unread_messages(self, telegram_id, direction):
        with self.session() as session:
            messages = session.query(TextMessage).filter(
                TextMessage.telegram_id == telegram_id,
                TextMessage.direction == direction,
                TextMessage.is_read == 0
            ).order_by(TextMessage.id.asc()).all()
            return messages
    
    def mark_messages_read(self, telegram_id, direction):
        with self.session() as session:
            messages = session.query(TextMessage).filter(
                TextMessage.telegram_id == telegram_id,
                TextMessage.direction == direction,
                TextMessage.is_read == 0
            ).all()
            for msg in messages:
                msg.is_read = 1
            session.commit()
    
    def get_latest_text_message(self, telegram_id, direction):
        with self.session() as session:
            message = session.query(TextMessage).filter(
                TextMessage.telegram_id == telegram_id,
                TextMessage.direction == direction
            ).order_by(TextMessage.id.desc()).first()
            return message
    
    def get_unsent_telegram_messages(self):
        """Получить все неотправленные сообщения для Telegram"""
        with self.session() as session:
            messages = session.query(TextMessage).filter(
                TextMessage.direction == "to_telegram",
                TextMessage.is_sent == 0
            ).order_by(TextMessage.id.asc()).all()
            return messages
    
    def mark_message_sent(self, message_id):
        """Отметить сообщение как отправленное"""
        with self.session() as session:
            message = session.query(TextMessage).filter(
                TextMessage.id == message_id
            ).first()
            if message:
                message.is_sent = 1
                session.commit()