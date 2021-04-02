# -*- coding: utf-8 -*-
import numpy as np
import time
import datetime
import gdown

from sklearn.preprocessing import LabelEncoder
from transformers import XLMRobertaTokenizer

import torch 
from torch.utils.data import DataLoader
from transformers import XLMRobertaForSequenceClassification, AdamW

def encode_text(text, tokenizer):
  return tokenizer(text, 
            max_length=128,
            add_special_tokens = True,
            truncation=True, 
            padding='max_length')
            
class Dataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        return item

    def __len__(self):
        return len(self.encodings)


def format_time(elapsed):
    '''
    Takes a time in seconds and returns a string hh:mm:ss
    '''
    # Round to the nearest second.
    elapsed_rounded = int(round((elapsed)))
    
    # Format as hh:mm:ss
    return str(datetime.timedelta(seconds=elapsed_rounded))
    

def predict(data_loader, model, device):
    predictions = []

    for batch in data_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)

        with torch.no_grad(): 
            outputs = model(input_ids, 
                            attention_mask=attention_mask, 
                            token_type_ids=None) 

        logits = outputs[0]                   
        logits = logits.detach().cpu().numpy()

        predictions.append(logits)

    return predictions


def get_le():
    le = LabelEncoder()
    le.classes_ = np.load('newsnet/text_classes.npy')
    return le


def kth_largest(predictions_i, k, le=get_le()):
    kth = np.argsort(-predictions_i, axis=1)[:, k-1]
    preds = le.inverse_transform(list(kth))
    if k != 1:
        mask = np.where(np.bincount(np.where(predictions_i > 0)[0]) != k)[0]
        preds = np.array(
            [None if i in mask else val for i, val in enumerate(preds)])

    return preds


def predict_pipeline(text, model):

    le = get_le()

    print("Downloading XLM-Roberta Tokenizer...")
    tokenizer = XLMRobertaTokenizer.from_pretrained('xlm-roberta-base')

    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Setting device to {device}")

    batch_size = min(len(text), 16)

    encoded = encode_text(text, tokenizer)
    dataset = Dataset(encoded)

    loader = DataLoader(dataset, batch_size=batch_size)
    predictions = predict(loader, model, device)

    preds = [np.argmax(predictions[i], axis=1).flatten()
            for i in range(len(text))]
    flat_preds = np.concatenate(preds).ravel()
    pred_cats1 = le.inverse_transform(flat_preds)

    pred_cats2 = [kth_largest(predictions[i], 2, le).flatten()
                    for i in range(len(predictions))]
    pred_cats2 = np.concatenate(pred_cats2).ravel()

    return pred_cats1, pred_cats2
