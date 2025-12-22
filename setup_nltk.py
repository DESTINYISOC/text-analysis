import nltk

def download_nltk_data():
    """Download required NLTK data for the application."""
    required_data = [
        'wordnet',
        'averaged_perceptron_tagger',
        'punkt',
        'stopwords'
    ]
    
    print("Downloading NLTK data...")
    for data in required_data:
        try:
            nltk.download(data, quiet=False)
            print(f"✓ Downloaded {data}")
        except Exception as e:
            print(f"✗ Failed to download {data}: {e}")

if __name__ == "__main__":
    download_nltk_data()