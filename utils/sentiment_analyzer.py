from transformers import pipeline, AutoTokenizer

# Load model and tokenizer
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model_name,
    tokenizer=model_name,
    top_k=None
)

tokenizer = AutoTokenizer.from_pretrained(model_name)

label_mapping = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

def analyze_sentiment(text):
    # Truncate manually to 512 tokens
    encoded_input = tokenizer(
        text,
        max_length=512,
        truncation=True,
        return_tensors='pt'
    )

    # Convert tokenized input back to string for pipeline (optional workaround)
    truncated_text = tokenizer.batch_decode(encoded_input['input_ids'], skip_special_tokens=True)[0]

    # Now safely run pipeline
    scores = sentiment_pipeline(truncated_text)[0]

    sentiment_scores = {
        label_mapping[entry["label"]]: round(entry["score"], 4)
        for entry in scores
    }

    predicted_label = max(sentiment_scores, key=sentiment_scores.get)

    return {
        "label": predicted_label,
        "scores": sentiment_scores
    }
