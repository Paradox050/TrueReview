from flask import Flask
from flask_pymongo import PyMongo
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
from dashboard.dashboard import init_dashboard
import gridfs
from routes.routes import register_routes
from controllers.google_oauth import init_oauth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB config
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
app.db = mongo.db
app.db = mongo.cx["TrueReview"]

# ✅ Check MongoDB connection
try:
    mongo.cx.server_info()
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", str(e))

# Google OAuth init
oauth, google = init_oauth(app)
app.oauth = oauth
app.google = google

# Register all routes
register_routes(app)
init_dashboard(app)

if __name__ == '__main__':
    app.run(debug=True)
