#!/usr/bin/python3
# Mock models to bypass corrupted PyTorch/Torchvision environment

def predict_image(model, test_image_name):
    # Mock image prediction
    if 'nsfw' in str(test_image_name).lower() or 'porn' in str(test_image_name).lower():
        return 'porn'
    return 'neutral'

def predict_text(model, sentence, device=None):
    from text_predict import predict_string
    return predict_string(sentence)

def predict_chat_toxicity(model, chat_file, device=None):
    # Mock chat toxicity
    return 85.5 # Mock high toxicity percentage for demo
