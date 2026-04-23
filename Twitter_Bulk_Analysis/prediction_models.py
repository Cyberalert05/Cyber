#!/usr/bin/python3
from transformers import pipeline
from PIL import Image
import torch

_nsfw_pipeline = None
_text_pipeline = None

def get_nsfw_pipeline():
    global _nsfw_pipeline
    if _nsfw_pipeline is None:
        device = 0 if torch.cuda.is_available() else -1
        _nsfw_pipeline = pipeline("image-classification", model="Falconsai/nsfw_image_detection", device=device)
    return _nsfw_pipeline

def get_text_pipeline():
    global _text_pipeline
    if _text_pipeline is None:
        device = 0 if torch.cuda.is_available() else -1
        _text_pipeline = pipeline("text-classification", model="unitary/toxic-bert", top_k=None, device=device)
    return _text_pipeline

def predict_image(model, test_image_name):
    pipe = get_nsfw_pipeline()
    if test_image_name.startswith('http://') or test_image_name.startswith('https://'):
        import requests
        from io import BytesIO
        response = requests.get(test_image_name)
        img = Image.open(BytesIO(response.content))
    else:
        img = Image.open(test_image_name)
    results = pipe(img)
    top_label = results[0]['label']
    
    if top_label.lower() == 'nsfw':
        return 'porn'
    else:
        return 'neutral'

def predict_text(model, sentence, device):
    pipe = get_text_pipeline()
    results = pipe(sentence)[0]
    
    toxic_score = 0
    for res in results:
        if res['label'] == 'toxic':
            toxic_score = res['score']
            break
            
    if toxic_score > 0.90:
        x = "highly toxic.Text is blocked"
    elif toxic_score > 0.50:
        x = "toxic"
    else:
        x = "Text does not violate the guidelines"
    return x

def predict_chat_toxicity(model, chat_file, device):
    import csv
    total = 0
    toxic = 0
    pipe = get_text_pipeline()
    try:
        with open(chat_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                message = row.get('message', '')
                if not message: continue
                results = pipe(message)[0]
                toxic_score = 0
                for res in results:
                    if res['label'] == 'toxic':
                        toxic_score = res['score']
                        break
                if toxic_score > 0.9:
                    toxic += 1
                total += 1
    except Exception as e:
        print(f"Error processing chat file: {e}")
        return 0
    
    if total == 0: return 0
    return (toxic / total) * 100
