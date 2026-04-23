#!/usr/bin/python3
# All Database connectors are here. Just call and run.
import pymongo
from datetime import datetime
import bcrypt
from exceptions import InvalidLoginError, UsernameTakenError


class Connection:
    """A connection to the database."""

    def __init__(self, app, host, port):
        self.app = app
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client['reportingapp']
        self.db_viraly = self.client['chat-app']
        self.complaints = self.db['complaints']
        self.posts = self.db_viraly['posts']
        self.messages = self.db_viraly['messages']

    def create_complaint(self,complaint):
        self.complaints.insert_one(complaint)

    def get_viraly_post(self,viraly_post_id):
        post = self.posts.find_one({'id':int(viraly_post_id)})
        return post
    
    def get_viraly_chat(self,viraly_chat_id):
        chat = self.messages.find({'room':viraly_chat_id},{'author':1,'date':1,'content':1})
        return chat

    def get_all_complaints(self):
        """Get all complaints sorted by most recent first."""
        complaints = list(self.complaints.find().sort('timestamp', -1).limit(200))
        for c in complaints:
            if '_id' in c:
                c['_id'] = str(c['_id'])
        return complaints

    def get_complaints_stats(self):
        """Get aggregated statistics for the forensic dashboard."""
        total = self.complaints.count_documents({})
        pending = self.complaints.count_documents({'status': 'pending'})
        resolved = self.complaints.count_documents({'status': 'resolved'})
        dismissed = self.complaints.count_documents({'status': 'dismissed'})
        
        # Platform breakdown
        pipeline = [
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}}
        ]
        platform_counts = {}
        for doc in self.complaints.aggregate(pipeline):
            platform_counts[doc['_id'] or 'unknown'] = doc['count']
        
        # Reason breakdown
        pipeline2 = [
            {'$group': {'_id': '$reason', 'count': {'$sum': 1}}}
        ]
        reason_counts = {}
        for doc in self.complaints.aggregate(pipeline2):
            reason_counts[doc['_id'] or 'unknown'] = doc['count']
        
        return {
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'dismissed': dismissed,
            'platforms': platform_counts,
            'reasons': reason_counts
        }

    def update_complaint_status(self, complaint_id, status):
        """Update the status of a complaint."""
        from bson import ObjectId
        self.complaints.update_one({'_id': ObjectId(complaint_id)}, {'$set': {'status': status}})
