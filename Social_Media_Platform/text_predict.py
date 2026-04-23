from transformers import pipeline
import torch

_toxic_pipeline = None

def get_pipeline():
    global _toxic_pipeline
    if _toxic_pipeline is None:
        device = 0 if torch.cuda.is_available() else -1
        _toxic_pipeline = pipeline("text-classification", model="unitary/toxic-bert", return_all_scores=True, device=device)
    return _toxic_pipeline

def predict_string(input_string):
    pipe = get_pipeline()
    results = pipe(input_string)[0]
    
    labels = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
    score_map = {res['label']: res['score'] for res in results}
    return [score_map.get(lbl, 0.0) for lbl in labels]
