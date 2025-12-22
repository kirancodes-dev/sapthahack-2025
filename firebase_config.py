import firebase_admin
from firebase_admin import credentials, firestore

# Check if Firebase is already initialized to avoid errors
if not firebase_admin._apps:
    try:
        # Load the key
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Connected via Config!")
    except Exception as e:
        print(f"❌ Firebase Config Error: {e}")

# Create the Database Client variable that other files will import
db = firestore.client()