import pickle
import os

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from django.shortcuts import HttpResponseRedirect

######################### GOOGLE DRIVE VARIABLES #########################

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secrets.json'
REDIRECT_URI = 'http://localhost:8000/report/'
API_NAME = 'drive'
API_VERSION = 'v3'

#requests authorization token from google drive 
def gdrive_auth_request():

    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(access_type='offline', prompt='select_account', include_granted_scopes='true')
    print("auth url: " + str(authorization_url))
    return HttpResponseRedirect(authorization_url)

def create_service(request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = REDIRECT_URI

    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    return build(API_NAME, API_VERSION, credentials=credentials)
