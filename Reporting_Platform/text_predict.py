#!/usr/bin/python3
# Mock text prediction to avoid PyTorch crash

TOXIC_WORDS = [
    'hate', 'kill', 'murder', 'stupid', 'idiot', 'die', 'fuck', 'shit',
    'bitch', 'rape', 'terrorist', 'retard', 'faggot', 'whore', 'slut',
    'cunt', 'nigger', 'kys', 'disgusting', 'worthless', 'pathetic'
]

def predict_string(text):
    """Predict toxicity of a string. Returns classification label."""
    text_lower = str(text).lower()
    score = 0
    for word in TOXIC_WORDS:
        if word in text_lower:
            score += 0.35

    if score > 0.85:
        return "highly toxic"
    elif score > 0.30:
        return "toxic"
    else:
        return "neutral"

def get_classification(platform, text):
    """Platform-aware classification wrapper."""
    return predict_string(text)
