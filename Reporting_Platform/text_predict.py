#!/usr/bin/python3
from transformers import pipeline
import torch

_toxic_pipeline = None

LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

def get_pipeline():
    global _toxic_pipeline
    if _toxic_pipeline is None:
        device = 0 if torch.cuda.is_available() else -1
        # top_k=None returns all labels (replaces deprecated return_all_scores)
        _toxic_pipeline = pipeline("text-classification", model="unitary/toxic-bert", top_k=None, device=device)
        print("[CODAR] BERT toxic-bert model loaded successfully.")
    return _toxic_pipeline

def predict_string(input_string):
    """Predict toxicity of a string. Returns dictionary of 6 category scores."""
    if not input_string or not str(input_string).strip():
        return {lbl: 0.0 for lbl in LABELS}
        
    try:
        pipe = get_pipeline()
        # Truncate to 512 chars to avoid token length errors
        results = pipe(str(input_string)[:512])
        
        # results is [[{label, score}, ...]] — a list containing one list of dicts
        scores_list = results[0] if isinstance(results[0], list) else results
        score_map = {item['label']: round(item['score'], 4) for item in scores_list}
        
        # Ensure all 6 labels are present
        for lbl in LABELS:
            if lbl not in score_map:
                score_map[lbl] = 0.0
        
        return score_map
    except Exception as e:
        print(f"[CODAR] BERT prediction error: {e}")
        return {lbl: 0.0 for lbl in LABELS}

def get_classification(platform, text):
    """Platform-aware classification wrapper."""
    return predict_string(text)

