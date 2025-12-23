import firebase_admin
from firebase_admin import credentials, firestore
import os

# Apply Windows Fix again to ensure DB thread safety
os.environ["GRPC_DNS_RESOLVER"] = "native"
os.environ["GRPC_POLL_STRATEGY"] = "poll"

# Singleton Pattern: Only initialize if not already running
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Database: CONNECTED")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        print("⚠️ Ensure 'serviceAccountKey.json' is in the project folder!")

db = firestore.client()