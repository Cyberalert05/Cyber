#!/usr/bin/python3
from flask import Flask, render_template, url_for, request, session, redirect, jsonify
import json
from bson import ObjectId
from database import Connection
from flask_pymongo import PyMongo   
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__,) 
db_host = os.getenv('MONGO_HOST', 'localhost')
db_port = os.getenv('MONGO_PORT', '27017')
app.config["MONGO_URI"] = f"mongodb://{db_host}:{db_port}/reportingapp"
mongo = PyMongo(app)
CORS(app)
db = mongo.db

@app.route('/whatsapp-table',methods=["GET","POST"])
def getWhatsapp():
    wapObj = []
    for i in db.complaints.find({"type": {"$in": ["Whatsapp", "whatsapp"]}}):
        wapObj.append({
            "timestamp": i.get("timestamp", ""),
            "victimName": i.get("victimName", ""),
            "harasserName": i.get("harasserName", ""),
            "victimDob": i.get("victimDob", ""),
            "link": i.get("link", ""),
            "type": i.get("type", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", "pending"),
            "hscore": i.get("hscore", "0")
        })
    #return jsonify(wapObj)
    return render_template("whatsapp-table.html", data = wapObj)
    #return render_template("whatsapp-table.html")


@app.route('/fb-table', methods=["GET", "POST"])
def getFb():
    fbobj = []
    for i in db.complaints.find({"type": {"$in": ["facebook", "Facebook"]}}):
        fbobj.append({
            "id": i.get("id", str(i.get("_id", ""))),
            "timestamp": i.get("timestamp", ""),
            "victimName": i.get("victimName", ""),
            "harasserName": i.get("harasserName", ""),
            "victimDob": i.get("victimDob", ""),
            "link": i.get("link", ""),
            "type": i.get("type", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", "pending"),
            "hscore": i.get("hscore", "0")
        })
    #return jsonify(fbobj)   
    return render_template("fb-table.html", data = fbobj) 


@app.route('/login', methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route('/viralry-table', methods=["GET", "POST"])
def getViraly():
    viralyObj = []
    for i in db.complaints.find({"type": {"$in": ["Viraly", "viraly"]}}):
        viralyObj.append({
            "id": i.get("id", str(i.get("_id", ""))),
            "victimName": i.get("victimName", ""),
            "harasserName": i.get("harasserName", ""),
            "victimDob": i.get("victimDob", ""),
            "link": i.get("link", ""),
            "type": i.get("type", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", "pending"),
            "hscore": i.get("hscore", "0")
        })
    #return jsonify(viralyObj)
    return render_template("viralry-table.html",data = viralyObj)


@app.route('/sms-table', methods=["GET", "POST"])
def getSms():
    smsObj = []
    for i in db.complaints.find({"type": {"$in": ["Sms", "sms"]}}):
        smsObj.append({
            "id": i.get("id", str(i.get("_id", ""))),
            "victimName": i.get("victimName", ""),
            "harasserName": i.get("harasserName", ""),
            "victimDob": i.get("victimDob", ""),
            "link": i.get("link", ""),
            "type": i.get("type", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", "pending"),
            "hscore": i.get("hscore", "0")
        })
    return render_template("sms-table.html",data = smsObj)


@app.route('/index', methods=["GET", "POST"])
def Index():
    c = {
        "uname": "Ford",
    }
    complaint_type = "Harrasment"
    return render_template("index.html", c=c, complaint_type=complaint_type)


@app.route('/twitter-table', methods=["GET", "POST"])
def getTwitter():
    twitterobj = []
    for i in db.complaints.find({"type": {"$in": ["twitter", "Twitter"]}}):
        twitterobj.append({
            "timestamp": i.get("timestamp", ""),
            "victimName": i.get("victimName", ""),
            "harasserName": i.get("harasserName", ""),
            "victimDob": i.get("victimDob", ""),
            "link": i.get("link", ""),
            "type": i.get("type", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", "pending"),
            "hscore": i.get("hscore", "0")
        })
    #return jsonify(twitterobj)
    return render_template("twitter-table.html", data = twitterobj)


@app.route('/',methods=["GET","POST"])
def getIndex():
    c = {
        "uname": "Ford",
    }
    complaint_type = "Harrasment"
    return render_template("index.html", c=c, complaint_type=complaint_type)

@app.route('/facebookReport', methods=["GET","POST"])
def preview():
    fbReport = []
    for i in db.complaints.find({"id": str(request.args.get('id'))}):
        fbReport.append({
            "victimFullName": i.get("victimFullName", ""),
            "victimName" : i.get("victimName", ""),
            "link" : i.get("link", ""),
            "harasserName" : i.get("harasserName", ""),
            "type": i.get("type", ""),
            "victimDob": i.get("victimDob", ""),
            "text": i.get("post_content", {}).get("post_text", "") if isinstance(i.get("post_content"), dict) else str(i.get("post_content", "")),
            "timestamp": i.get("timestamp", ""),
            "victimAddress": i.get("victimAddress", ""),
            "victimState": i.get("victimState", ""),
            "victimCity": i.get("victimCity", ""),
            "victimPincode": i.get("victimPincode", ""),
            "reason": i.get("reason", ""),
            "status": i.get("status", ""),
            "hscore": i.get("hscore", "0"),
            "post_type": i.get("post_content", {}).get("post_type", "") if isinstance(i.get("post_content"), dict) else "",
            "text_toxicity": i.get("post_content", {}).get("text_toxicity", "") if isinstance(i.get("post_content"), dict) else "",
            "image_prediction": i.get("post_content", {}).get("image_prediction", [0,0,0,0]) if isinstance(i.get("post_content"), dict) else [0,0,0,0],
            "image_link": i.get("post_content", {}).get("link", "") if isinstance(i.get("post_content"), dict) else "",
            "victimEmail": i.get("victimEmail", "")
        })
    return render_template("facebookReport.html", data = fbReport)


# ==================== SHIELD AI DETECTIONS ====================
@app.route('/shield-detections', methods=["GET"])
def getShieldDetections():
    """Show all CODAR Shield browser extension detections."""
    shield_platforms = ['twitter', 'youtube', 'instagram', 'whatsapp', 'facebook', 'browser_extension', 'generic']
    detections = []
    for i in db.complaints.find({"$or": [
        {"source": "codar_shield_extension"},
        {"platform": {"$in": shield_platforms}}
    ]}).sort("date", -1).limit(200):
        i['_id'] = str(i['_id'])
        detections.append(i)
    return jsonify(detections)


@app.route('/api/stats', methods=["GET"])
def getStats():
    """Return aggregated stats for all platforms."""
    total = db.complaints.count_documents({})
    pending = db.complaints.count_documents({"status": "pending"})
    resolved = db.complaints.count_documents({"status": "resolved"})
    
    pipeline = [{"$group": {"_id": "$type", "count": {"$sum": 1}}}]
    platform_counts = {}
    for doc in db.complaints.aggregate(pipeline):
        platform_counts[doc['_id'] or 'unknown'] = doc['count']
    
    # Also count by 'platform' field (extension uses this)
    pipeline2 = [{"$group": {"_id": "$platform", "count": {"$sum": 1}}}]
    for doc in db.complaints.aggregate(pipeline2):
        key = doc['_id'] or 'unknown'
        if key not in platform_counts:
            platform_counts[key] = doc['count']
    
    return jsonify({
        "total": total,
        "pending": pending,
        "resolved": resolved,
        "platforms": platform_counts
    })


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host='0.0.0.0',debug=True,port=3007)

