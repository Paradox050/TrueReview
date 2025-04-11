import subprocess
import json
import os
import pandas as pd
from utils.sentiment_analyzer import analyze_sentiment
from utils.csv_writer import save_to_csv

def analyze_product_reviews(url):
    try:
        # 📁 Set path to the node_scraper folder
        scraper_dir = os.path.join(os.getcwd(), "node_scraper")

        # ▶️ Run the Node.js scraper from within node_scraper directory
        subprocess.run(["node", "scraper.js", url], cwd=scraper_dir, check=True)
    except subprocess.CalledProcessError as e:
        return {"error": "Scraping failed", "details": str(e)}, 500

    try:
        # 📖 Load the scraped reviews from amazon_reviews.json inside node_scraper
        with open(os.path.join(scraper_dir, "amazon_reviews.json"), encoding='utf-8') as file:
            reviews = json.load(file)
    except Exception as e:
        return {"error": "Failed to read reviews", "details": str(e)}, 500

    # 🧠 Run sentiment analysis
    results = []
    for review in reviews:
        analysis = analyze_sentiment(review["text"])
        results.append({
            **review,
            "sentiment": analysis["label"],
            "positive_score": analysis["scores"]["Positive"],
            "neutral_score": analysis["scores"]["Neutral"],
            "negative_score": analysis["scores"]["Negative"]
        })

    # 💾 Save to CSV
    save_to_csv(results)
    return results
