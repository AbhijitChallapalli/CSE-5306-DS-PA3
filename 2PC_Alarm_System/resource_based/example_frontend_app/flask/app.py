import secrets
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests

ALARM_DIST_SYSTEM_URL = "http://api_gateway:5000"

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app, origins=["http://localhost:8080"])

@app.get("/")
@app.get("/index")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.get("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user_id=session["user_id"])

@app.post("/users/register")
def register_user():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    resp = requests.post(f"{ALARM_DIST_SYSTEM_URL}/users/register", json={
        "username": username,
        "password": password
    })

    if resp.status_code == 409:
        return jsonify({"error": "User already exists"}), 409
    elif resp.status_code in [200, 201]:
        session["user_id"] = resp.json()["id"]
        return jsonify({"success": True}), 201
    else:
        return jsonify({"error": "Unknown error"}), 500

@app.post("/users/authenticate")
def authenticate_user():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    resp = requests.post(f"{ALARM_DIST_SYSTEM_URL}/users/authenticate", json={
        "username": username,
        "password": password
    })

    if resp.status_code == 401:
        return jsonify({"error": "Invalid credentials"}), 401
    elif resp.status_code in [200, 201]:
        session["user_id"] = resp.json()["id"]
        return jsonify({"success": True}), 201
    else:
        return jsonify({"error": "Unknown error"}), 500

@app.get("/users/logout")
def logout_user():
    session.clear()
    return redirect(url_for("index"))

@app.get("/alarms/<int:alarm_id>")
def get_alarm(alarm_id: int):
    if "user_id" not in session:
        return redirect(url_for("index"))
    resp = requests.get(f"{ALARM_DIST_SYSTEM_URL}/alarms/{alarm_id}")
    return jsonify(resp.json()), resp.status_code

@app.get("/alarms/pending")
def get_pending_alarms():
    if "user_id" not in session:
        return redirect(url_for("index"))

    user_id = session["user_id"]
    resp = requests.get(f"{ALARM_DIST_SYSTEM_URL}/alarms?user_id={user_id}&status=pending")

    return jsonify(resp.json()), resp.status_code

@app.post("/alarms")
def create_alarm():
    if "user_id" not in session:
        return redirect(url_for("index"))

    data = request.get_json()
    resp = requests.post(
        f"{ALARM_DIST_SYSTEM_URL}/alarms",
        json={
            "user_id": session["user_id"],
            "time": data["time"],
            "message": data["message"]
        }
    )

    return jsonify(resp.json()), resp.status_code

@app.put("/alarms/<int:alarm_id>")
def update_alarm(alarm_id: int):
    if "user_id" not in session:
        return redirect(url_for("index"))
    data = request.get_json()
    resp = requests.put(
        f"{ALARM_DIST_SYSTEM_URL}/alarms/{alarm_id}",
        json={
            "user_id": session["user_id"],
            "time": data["time"],
            "message": data["message"]
        }
    )
    return jsonify(resp.json()), resp.status_code

@app.delete("/alarms/<int:alarm_id>")
def delete_alarm(alarm_id: int):
    if "user_id" not in session:
        return redirect(url_for("index"))
    resp = requests.delete(f"{ALARM_DIST_SYSTEM_URL}/alarms/{alarm_id}")
    return jsonify(resp.json()), resp.status_code

@app.get("/notifications")
def get_notifications():
    if "user_id" not in session:
        return redirect(url_for("index"))

    user_id = session["user_id"]
    resp = requests.get(f"{ALARM_DIST_SYSTEM_URL}/notifications?user_id={user_id}")

    return jsonify(resp.json()), resp.status_code

@app.delete("/notifications/<int:notif_id>")
def delete_notification(notif_id: int):
    if "user_id" not in session:
        return redirect(url_for("index"))
    resp = requests.delete(f"{ALARM_DIST_SYSTEM_URL}/notifications/{notif_id}")
    return jsonify(resp.json()), resp.status_code
