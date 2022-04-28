import pickle
import os
import io

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.shortcuts import redirect

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secrets.json'
REDIRECT_URI = 'http://localhost:8000/report/'
API_NAME = 'drive'
API_VERSION = 'v3'

#requests authorization token from google drive 
def get_auth_url():
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(access_type='offline', prompt='select_account', include_granted_scopes='true')
    return authorization_url

def create_service(request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = REDIRECT_URI

    flow.fetch_token(code=request.GET['code'])
    credentials = flow.credentials
    return build(API_NAME, API_VERSION, credentials=credentials)

def upload_to_gdrive(fileTitle, driveObj, csvObj):
    fileMetaData = {
        'name': fileTitle,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }

    csvString = csvObj.getvalue().strip('\r\n')
    bio = io.BytesIO(csvString.encode('utf-8'))
    csvUpload = MediaIoBaseUpload(bio, mimetype='text/csv', resumable=True)
    driveObj.files().create(body=fileMetaData, media_body=csvUpload).execute()
