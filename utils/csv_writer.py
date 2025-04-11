import pandas as pd

def save_to_csv(data, filename="sentiment_results.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"📁 {filename} saved successfully.")
