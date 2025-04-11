from authlib.integrations.flask_client import OAuth
from flask import url_for, session, redirect, request
import os

def init_oauth(app):
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    return oauth, google

def handle_google_authorize(app, google):
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo') or google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        if user_info:
            session['user'] = user_info
            app.db.users.update_one(
                {'email': user_info.get('email')},
                {'$set': {
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'sub': user_info.get('sub')
                }},
                upsert=True
            )
            return redirect('/')
        else:
            return "Failed to fetch user info", 400
    except Exception as e:
        print("❌ OAuth error:", e)
        return "Authorization failed", 500
