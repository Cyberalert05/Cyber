#!/usr/bin/python3
"""
All functions related to Viraly go here
"""

def get_data_viraly(db, content_type, viraly_id):
    """ Fetch data for a viraly post or chat and return a structured dict.
    Raises ValueError for unknown content types.
    """
    viraly_url = "http://localhost:3069/"
    post_content = {}

    if content_type == "post":
        post = db.get_viraly_post(viraly_id)
        if post is None:
            raise ValueError(f"Viraly post with id '{viraly_id}' not found in database.")
        post_content = {
            'content_type': content_type,
            'post_id': viraly_id,
            'post_type': post['content']['posttype'],
            'post_text': post['content']['postcontent'],
            'post_media': viraly_url + post['content']['medialink']
        }
    elif content_type == "message":
        import csv
        import os

        chat = db.get_viraly_chat(viraly_id)
        # Create user content folder
        if not os.path.exists("static/user-content"):
            os.makedirs("static/user-content")
        chat_csv_path = "static/user-content/" + viraly_id + '.csv'
        with open(chat_csv_path, 'w', newline='', encoding='utf-8') as chat_csv:
            writer = csv.writer(chat_csv)
            for message in chat:
                writer.writerow((message['date'], message['author'], message['content']))
        post_content = {
            'content_type': content_type,
            'chat_id': viraly_id,
            'chat_file': viraly_url + "static/user-content/" + viraly_id + '.csv'
        }
    else:
        raise ValueError(f"Unknown viraly content_type: '{content_type}'. Expected 'post' or 'message'.")

    return post_content


