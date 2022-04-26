from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from inventory.models import Family, Category, Item, ItemTransaction, Checkin, Checkout
import os
from datetime import datetime
from zipfile import ZipFile
from email.mime.application import MIMEApplication
import shutil

MODELS_TO_BACKUP = [Family, Category, Item, ItemTransaction, Checkin, Checkout]
DIR_HERE = os.path.dirname(__file__)
BACKUPSQL_NAME = 'backup_db.sqlite3'
ZIPFILE_NAME = 'backup.zip'
DIR_HERE = os.path.dirname(__file__)
PATH = os.path.abspath(os.path.join(DIR_HERE, '../../../db_backups'))

class Command(BaseCommand):
    args = 'this function takes one argument, which is the email you want to send the backups to'
    help = 'Try `python3 manage.py db_backup EMAIL_ADDRESS`'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def copy_db(self):
        # print("PATH: " + PATH)
        # print("SQL PATH: " + os.path.join(PATH, BACKUPSQL_NAME))
        # print("ZIP PATH: " + os.path.join(PATH, ZIPFILE_NAME))
        if not os.path.exists('db_backups'):
            os.makedirs('db_backups')
        shutil.copyfile("./db.sqlite3", os.path.join(PATH, BACKUPSQL_NAME))
    
    def zip_files(self):
        with ZipFile(os.path.join(PATH, ZIPFILE_NAME),'w') as zip:
            zip.write(os.path.join(PATH, BACKUPSQL_NAME))

    def send_email(self, to_email_addr):
        date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        email = EmailMessage(
            f'Database backup \'s: {date}',
            f'Please find attached zipped database backups of the FLP inventory system as of {date}. ',
            'flpinventory@gmail.com',
            [to_email_addr],
            [],
            reply_to=['flpinventory@gmail.com'],
            headers={},
        )
        with open(os.path.join(PATH, ZIPFILE_NAME),'rb') as file:
            email.attach(MIMEApplication(file.read(), Name=ZIPFILE_NAME))
        email.send()


    def handle(self, *args, **options):
        addr = options['email']
        self.copy_db()
        self.zip_files()
        self.send_email(addr)
