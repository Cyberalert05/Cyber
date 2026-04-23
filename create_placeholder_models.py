#!/usr/bin/python3
"""
Creates placeholder ML models so the CODAR apps can start without crashing.
These are dummy models that will return random predictions.
Replace with real trained models for actual use.
"""
import torch
import torch.nn as nn
from torchvision import models
import os

def create_nsfw_model(save_path):
    """Create a placeholder NSFW image classification model (ResNet50-based)."""
    model = models.resnet50(weights=None)
    # Modify final layer for 5 classes: drawing, hentai, neutral, porn, sexy
    model.fc = nn.Linear(model.fc.in_features, 5)
    model.fc = nn.Sequential(
        nn.Linear(model.fc[0].in_features if isinstance(model.fc, nn.Sequential) else model.fc.in_features, 5),
        nn.LogSoftmax(dim=1)
    )
    # Re-create with simpler approach
    model = models.resnet50(weights=None)
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_features, 5),
        nn.LogSoftmax(dim=1)
    )
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model, save_path)
    print(f"[OK] Created placeholder NSFW model at: {save_path}")

def create_text_model(save_path):
    """Create a placeholder BERT text toxicity model checkpoint."""
    from transformers import BertForSequenceClassification
    
    # Create a simple BERT model for sequence classification
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-multilingual-uncased',
        num_labels=2
    )
    
    state_dict = model.state_dict()
    state_dict = {f"encoder.{k}": v for k, v in state_dict.items()}
    checkpoint = {
        'model_state_dict': state_dict,
        'valid_loss': 0.5
    }
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(checkpoint, save_path)
    print(f"[OK] Created placeholder text model at: {save_path}")

if __name__ == "__main__":
    # Create models for Social_Media_Platform
    create_nsfw_model("Social_Media_Platform/models/model_nsfw.pt")
    create_text_model("Social_Media_Platform/models/model_initial_text.pt")
    
    # Create models for Reporting_Platform
    create_nsfw_model("Reporting_Platform/models/model_nsfw.pt")
    create_text_model("Reporting_Platform/models/model_initial_text.pt")
    
    # Create models for Twitter_Bulk_Analysis
    create_nsfw_model("Twitter_Bulk_Analysis/models/model_nsfw.pt")
    create_text_model("Twitter_Bulk_Analysis/models/model_initial_text.pt")
    
    print("\n[SUCCESS] All placeholder models created successfully!")
    print("[WARNING] These are DUMMY models with random weights.")
    print("    Replace with real trained models for actual predictions.")
