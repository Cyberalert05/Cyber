#!/usr/bin/python3
import whatsapp, twitter, facebook as fb, viraly, sms
from database import Connection
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, request, session, make_response, flash
import hashlib
import json
import tweepy
import re
import csv
import os
import prediction_models
from datetime import datetime
import text_predict
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
app.secret_key='somerandomvalue'
app.config['UPLOAD_FOLDER'] = 'user-content/'

# Enable CORS for cross-origin reporting from Viraly & Browser Extension
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
    return response

tw_ckey = os.getenv('TWITTER_CONSUMER_KEY', 'QLZOw8V2qWMqkz16vN68PktsV')
tw_csecret = os.getenv('TWITTER_CONSUMER_SECRET', 'WTDuUbYtiWS34b1lj8aFiCC6aO5ne3TrTAA9O5KRcbEho4urmJ')
tw_atoken = os.getenv('TWITTER_ACCESS_TOKEN', '1072128142108545025-WQLw8ItTTHhHeJqDjBUdq1FIeCGeGj')
tw_asecret = os.getenv('TWITTER_ACCESS_SECRET', 'FW4REiWqSPxOQmjGqdOLQhf7YmMP1AgVY80OdUcKV36xL')

auth = tweepy.OAuthHandler(tw_ckey, tw_csecret)    
auth.set_access_token(tw_atoken, tw_asecret) 

twapi = tweepy.API(auth,wait_on_rate_limit=True)

db_host = os.getenv('MONGO_HOST', 'localhost')
db_port = int(os.getenv('MONGO_PORT', 27017))
db = Connection(app, db_host, db_port) 
quick_launch = True

# Models are handled by prediction_models and text_predict internally.

# Push to Database Functions
def db_push_commons(username, email, full_name, date_of_birth, address, 
                state, city, pincode, crime_type, platform, link ,post_content):
    """ Push Common Data for all platforms database
    """
    from random import randint
    complaint = {
        'id': str(randint(10000, 99999)),
        'timestamp': datetime.now(),
        'victimName':username,
        'harasserName': "kk",
        'victimEmail':email,
        'victimFullName':full_name,
        'victimDob':date_of_birth,
        'victimAddress':address,
        'victimState':state,
        'victimCity':city,
        'victimPincode':pincode,
        'reason':crime_type,
        'type':platform,
        'link': link,
        'status':'pending',
        'hscore':'0.5',
        'post_content':post_content
    }
    print(complaint)
    db.create_complaint(complaint)


# 404: Page not found handler
@app.errorhandler(404)
def not_found(e):
    return render_template("errorpages/404.html")

def get_classification(platform,post_content):
    if(platform=="twitter"):
        post_content_prediction = text_predict.predict_string(post_content['post_text'])
        image_prediction = [0,0,0,0]
        if(post_content['tweet_type']=="image"):
            image_prediction = prediction_models.predict_image(None,post_content['post_media'])
        post_content['text_toxicity'] = post_content_prediction
        post_content['image_prediction'] = image_prediction

    if(platform=="viraly"):
        post_content_prediction = text_predict.predict_string(post_content['post_text'])
        image_prediction = [0,0,0,0]
        if(post_content['post_type']=="media"):
            image_prediction = prediction_models.predict_image(None,post_content['post_media'])
        post_content['text_toxicity'] = post_content_prediction
        post_content['image_prediction'] = image_prediction

    if(platform=="whatsapp"):
        text_toxicity = prediction_models.predict_chat_toxicity(None,post_content['uploaded_chat'],None)
        post_content['text_toxicity'] = text_toxicity

    if(platform=="facebook"):
        post_content_prediction = text_predict.predict_string(post_content['post_text'])
        image_prediction = [0,0,0,0]
        if(post_content['post_type']=="image"):
            print('hello')
            image_prediction = prediction_models.predict_image(None,post_content['post_media'])
        post_content['text_toxicity'] = post_content_prediction
        post_content['image_prediction'] = image_prediction


    return post_content


@app.route('/push', methods=['POST', 'OPTIONS']) 
def form_entry():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method == 'POST':
        # Detect if this is an AJAX request (from Viraly modal)
        is_ajax = request.headers.get('Origin') or request.headers.get('X-Requested-With')
        
        platform = request.form.get('platform', 'unknown')

        # Form data retrieval from POST (with safe defaults)
        username        = request.form.get('username', 'anonymous')
        email           = request.form.get('email', '')
        full_name       = request.form.get('full_name', '')
        date_of_birth   = request.form.get('dob', '')
        address         = request.form.get('address', '')
        state           = request.form.get('state', '')
        city            = request.form.get('city', '')
        pincode         = request.form.get('pincode', '')
        crime_type      = request.form.get('crime_type', 'Harrasment')
        link = ''  # always defined, each branch overwrites as needed
        try:
            if(platform=="twitter"):    
                link = request.form['tweet_link']
                post_content = twitter.get_data_twitter(request.form['tweet_link'], twapi)
                post_content = get_classification(platform,post_content)
            elif(platform=="facebook"): 
                link = request.form['fb_link']
                encoded_link =  request.form['post_encoded_url']
                post_content = fb.get_data_facebook(encoded_link,link)
                post_content = get_classification(platform,post_content)
            elif(platform=="viraly"):   
                link = request.form.get('viraly_post_id', '')
                content_type = request.form.get('viraly_content-type', 'post')
                try:
                    post_content = viraly.get_data_viraly(db, content_type, link)
                    post_content = get_classification(platform, post_content)
                except Exception as e:
                    print(f"[CODAR] Viraly data retrieval error: {e}")
                    # Fallback: create a basic post_content from form data
                    post_content = {
                        'content_type': content_type,
                        'post_id': link,
                        'post_text': request.form.get('additional_details', ''),
                        'text_toxicity': 'reported_by_user',
                        'source': 'manual_report'
                    }
            elif(platform=="whatsapp"): 
                link = "http://localhost:3003/static/user-content/"+username+"/"+request.files['whatsapp_backup'].filename
                post_content = whatsapp.get_data_whatsapp(username,request.files['whatsapp_backup'],app.config['UPLOAD_FOLDER'])
                post_content = get_classification(platform,post_content)
            elif(platform == "youtube"):    
                link = request.form.get('youtube_link', '')
                yt_link = link
                from youtube import Youtube
                yt = Youtube()
                temp = yt.auto_yt(yt_link, None, pretty=True)
                return render_template("video-result.html", temp=temp, yt_link=yt_link)
            elif(platform == "sms"):    
                link = request.form.get('sender_number', '')
                post_content = sms.get_data_sms(link)
            else:                       
                post_content = {'report': request.form.get('additional_details', ''), 'source': 'manual'}
            
            db_push_commons(username, email, full_name, date_of_birth,
                address, state, city, pincode, crime_type, platform, link, post_content)
            
            # Return JSON for AJAX, redirect for traditional form
            if is_ajax:
                from flask import jsonify
                resp = jsonify({'success': True, 'message': 'Report submitted successfully'})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp, 200
            return redirect(url_for('index_main'))
            
        except Exception as e:
            print(f"[CODAR] Push error: {e}")
            import traceback
            traceback.print_exc()
            if is_ajax:
                from flask import jsonify
                resp = jsonify({'success': False, 'error': str(e)})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp, 500
            flash(f'Error processing report: {str(e)}')
            return redirect(url_for('index_main'))
    else:
        return redirect(url_for('index_main'))


@app.route('/', methods=['GET'])
def index_main():
    if request.method == 'GET': 
        platform = request.args.get('platform')
        print(platform)
        # Render the right template
        if platform==None or platform=="twitter":   return render_template("twitter.html", platform="twitter")
        elif platform=="sms":                       return render_template("phone-message.html", platform=platform)
        elif platform=="viraly":                    return render_template("viraly.html", platform=platform)
        elif platform=="facebook":                  return render_template("facebook.html", platform=platform)
        elif platform=="whatsapp":                  return render_template("whatsapp.html", platform=platform)
        elif platform=="youtube":                   return render_template("youtube.html", platform=platform)
        else:                                       return render_template("under-construction.html", platform=platform)
    else:
        return render_template("twitter.html", platform=platform)
        

# ==================== BROWSER EXTENSION API ====================
@app.route('/api/extension-report', methods=['POST'])
def extension_report():
    """Receive bulk toxicity reports from the CODAR Shield browser extension."""
    from flask import jsonify
    import json
    from datetime import datetime
    
    try:
        data = request.get_json(force=True)
    except:
        data = None
    
    if not data:
        return jsonify({'error': 'No data received'}), 400
    
    page_url = data.get('page_url', 'unknown')
    page_title = data.get('page_title', 'unknown')
    flagged_items = data.get('flagged_items', [])
    
    # Use the actual detected platform (twitter, youtube, instagram, whatsapp, facebook, generic)
    detected_platform = data.get('platform', 'browser_extension')
    platform_name = data.get('platform_name', 'Browser Extension')
    
    complaints_created = 0
    for item in flagged_items:
        text = item.get('text', '')
        
        # Run the text through our actual BERT model
        text_toxicity_scores = {}
        if text:
            import text_predict
            text_toxicity_scores = text_predict.predict_string(text)
            
        complaint = {
            'platform': detected_platform,
            'platform_name': platform_name,
            'source': 'codar_shield_extension',
            'page_url': page_url,
            'page_title': page_title,
            'crime_type': 'Auto-detected toxicity',
            'status': 'pending',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scan_time': data.get('scan_time', ''),
            'total_flagged_on_page': data.get('total_flagged', 0),
            
            # Map into the expected dashboard structure
            'type': detected_platform, 
            'victimName': 'Browser Extension User',
            'post_content': {
                'post_text': text,
                'text_toxicity': text_toxicity_scores,
                'source': 'extension'
            }
        }
        db.create_complaint(complaint)
        complaints_created += 1
    
    return jsonify({
        'success': True,
        'complaints_created': complaints_created,
        'message': f'{complaints_created} complaints filed successfully'
    }), 200

# ==================== FORENSIC DASHBOARD ====================
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the CODAR Forensic Reporting Dashboard."""
    complaints = db.get_all_complaints()
    stats = db.get_complaints_stats()
    return render_template("dashboard.html", complaints=complaints, stats=stats)

@app.route('/api/update_complaint', methods=['POST'])
def update_complaint():
    """Update complaint status via AJAX."""
    from flask import jsonify
    try:
        data = request.get_json(force=True)
        complaint_id = data.get('id')
        status = data.get('status')
        if not complaint_id or not status:
            return jsonify({'success': False, 'error': 'Missing data'}), 400
        
        db.update_complaint_status(complaint_id, status)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating complaint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=3003, use_reloader=True, debug=True)
