import logging
import os
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote_plus

from dotenv import load_dotenv

from app.logger import setup_logging

load_dotenv()


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__()
        return cls._instance


class EmailService(metaclass=Singleton):
    class _Connection(smtplib.SMTP_SSL):
        def __init__(self):
            super().__init__(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
            self._reconnect()
            self.logging = setup_logging(name="EmailService")
            self.logging.info(f'Connected SMTP server')

        def _reconnect(self):
            super().connect(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
            # super().starttls()
            super().login(os.getenv("EMAIL_LOGIN"), os.getenv("EMAIL_PASSWORD"))

        @staticmethod
        def is_connected(conn):
            try:
                status = conn.noop()[0]
            except smtplib.SMTPServerDisconnected as e:
                status = -1
            return True if status == 250 else False

        def __enter__(self):
            if not self.is_connected(self):
                self._reconnect()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    def __init__(self):
        self.connection = self._Connection()

    def send_verification_email_code(self, code_confirm, to_addr):
        try:
            with self.connection as server:
                subject = 'Запрос на подтверждения почты ProjectDelta'
                body = (f'Ваш код подтверждения: {code_confirm}'
                        '\n\nХорошего дня!')

                # Create a MIMEText object with UTF-8 encoding
                msg = MIMEText(body, 'plain', 'utf-8')

                # Set the email subject and message
                msg['Subject'] = subject
                msg['From'] = 'pojectdelta@ya.ru'
                msg['To'] = to_addr
                server.send_message(msg, to_addrs=to_addr)
        except Exception as e:
            print("Неудалось отправить, код :", code_confirm)

    def send_reset_password_code(self, code_reset, to_addr):
        try:
            with self.connection as server:
                subject = 'Запрос на сброс пароля ProjectDelta'
                body = (f'Ваш код: {code_reset}'
                        '\n\nХорошего дня!')

                # Create a MIMEText object with UTF-8 encoding
                msg = MIMEText(body, 'plain', 'utf-8')

                # Set the email subject and message
                msg['Subject'] = subject
                msg['From'] = 'pojectdelta@ya.ru'
                msg['To'] = to_addr
                server.send_message(msg, to_addrs=to_addr)
        except Exception as e:
            print("Неудалось отправить, код :", code_reset)

    def send_link_tg_code(self, code_confirm, to_addr):
        try:
            with self.connection as server:
                subject = 'Запрос на подтверждения tg ProjectDelta'
                body = (f'Ваш код подтверждения: {code_confirm}'
                        '\n\nХорошего дня!')

                # Create a MIMEText object with UTF-8 encoding
                msg = MIMEText(body, 'plain', 'utf-8')

                # Set the email subject and message
                msg['Subject'] = subject
                msg['From'] = 'pojectdelta@ya.ru'
                msg['To'] = to_addr
                server.send_message(msg, to_addrs=to_addr)
        except Exception as e:
            print("Неудалось отправить, код :", code_confirm)


if __name__ == '__main__':
    email_service = EmailService()
    email_service.send_verification_email_code(123456, 'makcc2002@gmail.com')
