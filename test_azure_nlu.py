import requests
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_KEY      = os.getenv("AZURE_LANGUAGE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")

print("=" * 50)
print("SAFEROAD AI - Azure Language Test")
print("=" * 50)

if not AZURE_KEY:
    print("[ERROR] Azure key not found!")
    exit()

print(f"[OK] Azure Key: {AZURE_KEY[:8]}...")

# Test text - road incident report
test_text = (
    "There is a serious accident on main street. "
    "Two cars crashed and there is smoke. "
    "People are injured and need help urgently."
)

print(f"[OK] Test text ready")
print("[..] Sending Request to Azure Language API...")

# API endpoint
url = (
    f"{AZURE_ENDPOINT}"
    "language/:analyze-text?api-version=2023-04-01"
)

# Request headers
headers = {
    "Ocp-Apim-Subscription-Key": AZURE_KEY,
    "Content-Type": "application/json"
}

# Request body
body = {
    "kind": "SentimentAnalysis",
    "parameters": {
        "modelVersion": "latest"
    },
    "analysisInput": {
        "documents": [
            {
                "id":       "1",
                "language": "en",
                "text":     test_text
            }
        ]
    }
}

# Send Request
try:
    response = requests.post(
        url,
        headers = headers,
        json    = body
    )
    result = response.json()

except Exception as e:
    print(f"[ERROR] {e}")
    exit()

# Error check
if "error" in result:
    print(f"[ERROR] {result['error']['message']}")
    exit()

# Show Results
print("")
print("=" * 50)
print("[SUCCESS] Azure Language API is working!")
print("=" * 50)

doc = result["results"]["documents"][0]

sentiment = doc["sentiment"]
scores    = doc["confidenceScores"]

print("")
print("[SENTIMENT ANALYSIS]")
print("-" * 40)
print(f"  Overall:  {sentiment.upper()}")
print(f"  Positive: {scores['positive']*100:.1f}%")
print(f"  Negative: {scores['negative']*100:.1f}%")
print(f"  Neutral:  {scores['neutral']*100:.1f}%")

print("")
print("[SENTENCES]")
print("-" * 40)

for i, sentence in enumerate(doc["sentences"], 1):
    text      = sentence["text"][:50]
    sentiment = sentence["sentiment"]
    print(f"  {i}. [{sentiment.upper()}] {text}")

print("")
print("=" * 50)
print("[DONE] Test complete!")
print("=" * 50)