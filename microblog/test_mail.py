import logging
from logging.handlers import SMTPHandler
from logging import StreamHandler
import os

MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

auth = None
if MAIL_USERNAME or MAIL_PASSWORD:
    auth = (MAIL_USERNAME, MAIL_PASSWORD)
secure = None
if MAIL_USE_TLS:
    secure = ()

mail_handler = SMTPHandler(
    mailhost=(MAIL_SERVER, MAIL_PORT),
    fromaddr='no-reply@' + MAIL_SERVER,
    toaddrs=["gdelozie@kent.edu"], subject='Example Log Entry',
    credentials=auth, secure=secure)
mail_handler.setLevel(logging.ERROR)

stream_handler = StreamHandler()
stream_handler.setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.addHandler(mail_handler)
logger.addHandler(stream_handler)

logger.error("This is a sample error")

import 