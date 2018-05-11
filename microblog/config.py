import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	SECRET_KEY = '5279b9fe290f4c84a7a4d15b926a4a45'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = 1
	MAIL_USERNAME = 'couchpotatoes.kentstate@gmail.com'
	MAIL_PASSWORD = 'Couchpotatoes@2018kentstate'
	ADMINS = ['couchpotatoes.kentstate@gmail.com']
	LANGUAGES = ['en', 'es']
	POSTS_PER_PAGE = 5
	MS_TRANSLATOR_KEY = '5279b9fe290f4c84a7a4d15b926a4a45'
	SECURITY_EMAIL_SENDER = 'couchpotatoes.kentstate@gmail.com'