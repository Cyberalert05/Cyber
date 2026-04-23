#!/usr/bin/python3
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import pymysql.cursors
import geocoder
import prediction_models
import text_predict
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

ckey= os.getenv('TWITTER_CONSUMER_KEY', '')
csecret= os.getenv('TWITTER_CONSUMER_SECRET', '')
atoken= os.getenv('TWITTER_ACCESS_TOKEN', '')
asecret= os.getenv('TWITTER_ACCESS_SECRET', '')

db_host = os.getenv('MYSQL_HOST', 'localhost')
db_user = os.getenv('MYSQL_USER', 'root')
db_pass = os.getenv('MYSQL_PASSWORD', '0000')
db_name = os.getenv('MYSQL_DB', 'tweet_monitoring')

connection = pymysql.connect(host=db_host,
                             port=3306,
                             user=db_user,
                             password=db_pass,
                             db=db_name,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# Models are loaded in text_predict and prediction_models.


class listener(StreamListener):

    def on_data(self, data):
        all_data = json.loads(data)
        if not all_data['retweeted'] and 'RT @' not in all_data['text']:
            if(all_data.get('lang')=='en' and len(all_data['entities']['hashtags'])>0):
                #print(json.dumps(all_data,indent=2,sort_keys=True))
                tweet_type = "text"
                tweet_timestamp = all_data.get("timestamp_ms")
                tweet_created = all_data.get("created_at")
                username = all_data.get('user').get('name')
                profile_picture = all_data.get('user').get('profile_image_url')
                media_url = ''
                tweet_text = all_data.get("text")
                if(all_data.get('extended_tweet',"None")!="None"):
                    tweet_text = all_data.get("extended_tweet").get("full_text")
                    if(all_data.get("extended_tweet").get('entities').get('media', "None") == "None"):
                        pass
                    else:
                        tweet_type = "image"
                        media_url = all_data.get("extended_tweet").get('entities').get('media')[0].get('media_url')
                        if(all_data.get("extended_tweet").get('entities').get('media')[0].get("type") == 'video'):
                            tweet_type = "video"
                            media_url = all_data.get("extended_tweet").get('entities').get('media')[0].get('video_info').get('variants')[0].get('url')
                hashtags = []
                raw_hashtags = all_data['entities']['hashtags']
                location = all_data.get('user').get('location')
                id_tweet = all_data.get('id')
                latitude = ""
                longitude = ""
                if(location!=None):

                    result = geocoder.arcgis(location)
                    if(result.x!=None and result.y!=None):
                        latitude = str(result.y)
                        longitude = str(result.x)
                else:
                    location = ''

                #Predicting toxicity for a post with image and text
                post_content_prediction = text_predict.predict_string(tweet_text)
                # predict_string returns a scalar score — no need for max()
                text_toxicity = post_content_prediction
                image_prediction = ''
                if(tweet_type=="image"):
                    image_prediction = prediction_models.predict_image(None, media_url)
                image_class = image_prediction

                try:
                    with connection.cursor() as cursor:
                        sql = "INSERT INTO `tweets` VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        dt_object = datetime.fromtimestamp(int(tweet_timestamp)/1000)
                        cursor.execute(sql,(id_tweet,dt_object,tweet_created,username,profile_picture,tweet_type,tweet_text,media_url,location,latitude,longitude,text_toxicity,image_class))
                        # if(location!=None and latitude!=None and longitude!=None):
                        #     sql = "INSERT INTO `tweets_location` VALUES (%
                        # s,%s,%s,%s)"
                        #     cursor.execute(sql, (id_tweet,location,latitude,longitude))
                        for i in raw_hashtags:
                            hashtags.append(i['text'])
                            sql = "INSERT INTO `hashtags` VALUES (%s)"
                            cursor.execute(sql, (i['text']))
                            # if(location!=None and latitude!=None and longitude!=None):
                            #     sql = "INSERT INTO `hashtags_location` VALUES (%s,%s,%s,%s)"
                            #     cursor.execute(sql,(i['text'],location,latitude,longitude))
                        connection.commit()
                finally:
                    pass
                print("Post ID:",id_tweet,"inserted!")
        return True

    def on_error(self, status):
        print (status)


auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)

twitterStream = Stream(auth, listener(),tweet_mode='extended')
twitterStream.filter(track=["covid-19"])
