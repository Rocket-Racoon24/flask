import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "testdb")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# URL-encode password
encoded_pass = quote_plus(MONGO_PASS) if MONGO_PASS else ""

# MongoDB connection URI
MONGO_URI = f"mongodb+srv://admin:a24@cluster0.qmeawqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
try:
    client.server_info()
    print("Connected to MongoDB Atlas ✅")
except ServerSelectionTimeoutError as e:
    print("Could not connect to MongoDB Atlas:", e)

# Configure Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    print("⚠️ No GEMINI_API_KEY set in environment. AI features will not work.")

# ---------------- WEB PAGE ROUTES ----------------

@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/logins-page")
def logins_page():
    return render_template("logins.html")

@app.route("/register.html", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email and password required"}), 400

        db_data = client["data"]
        logins_coll = db_data["logins"]
        logins_coll.insert_one({
            "email": data["email"],
            "password": data["password"]
        })

        return jsonify({"message": "Registration saved successfully"}), 201

@app.route("/ask", methods=["GET", "POST"])
def ask_ai():
    if request.method == "GET":
        return render_template("index.html")
    
    data = request.get_json()
    user_message = data.get("message", "")

    ai_reply = ""
    try:
        if not GEMINI_API_KEY:
            return jsonify({"reply": "AI not configured. Please set GEMINI_API_KEY."})
        
        response = model.generate_content(user_message)
        ai_reply = response.text

        # Save to MongoDB
        db_data = client["data"]
        ai_coll = db_data["ai"]
        ai_coll.insert_one({
            "question": user_message,
            "reply": ai_reply
        })
    except Exception as e:
        ai_reply = f"Error: {str(e)}"

    return jsonify({"reply": ai_reply})

@app.route("/get-logins", methods=["GET"])
def get_logins():
    db_data = client["data"]
    logins_coll = db_data["logins"]
    logins = list(logins_coll.find({}, {"_id": 0}))
    return jsonify(logins)

@app.route("/ai-data")
def ai_data_page():
    return render_template("ai_data.html")  # HTML page

@app.route("/get-ai-data", methods=["GET"])
def get_ai_data():
    db_data = client["data"]  # 'data' DB
    ai_coll = db_data["ai"]   # 'ai' collection

    # Fetch all documents without MongoDB's _id
    records = list(ai_coll.find({}, {"_id": 0}))
    return jsonify(records)




if __name__ == "__main__":
    app.run(debug=False, threaded=False)
