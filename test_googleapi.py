# Google Vision API Test
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error in API Key")
    print("Please check .env file")
    exit()
print(f" API KEY found: {GOOGLE_API_KEY}")

TEST_IMAGE_URL = "https://cloud.google.com/static/vision/docs/images/setagaya_small.jpeg"

print(f" Test image: {TEST_IMAGE_URL}")
print("Sending Request to Google Vision API...")

API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"

request_body = {
    "requests": [           # List-can send multiple images
        {
            "image": {
                "source": {
                    "imageUri": TEST_IMAGE_URL  # Image URL
                }
            },
            "features": [   # what features to detect 
                {
                    "type": "LABEL_DETECTION",    # Objects & scenes
                    "maxResults": 10              # Maximum 10 labels
                },
                {
                    "type": "OBJECT_LOCALIZATION", # Objects location
                    "maxResults": 5
                },
                {
                    "type": "SAFE_SEARCH_DETECTION" # Dangerous content check
                }
            ]
        }
    ]
}
try:
    # send POST request
    response = requests.post(
        API_URL,           # where to send
        json=request_body  # what to send
    )
    
    # Convert Response to Python dictionary
    result = response.json()
    
except Exception as e:
    print(f" Network error: {e}")
    print("  Check Internet connection")
    exit()

if "error" in result:
    error_msg = result["error"]["message"]
    error_code = result["error"]["code"]
    
    print(f"\n API Error!")
    print(f"   Code: {error_code}")
    print(f"   Message: {error_msg}")
    
    if error_code == 400:
        print("   → API key is wrong")
    elif error_code == 403:
        print("   → Vision API is not enabled")
    elif error_code == 429:
        print("   → Quota is expired")
    exit()

print("\n" + "="*50)
print("✅ Google Vision API is Working!")
print("="*50)

api_response = result["responses"][0]

# --- LABELS (Image ) ---
print("\n📋 DETECTED LABELS (Features in Image):")
print("-" * 40)

labels = api_response.get("labelAnnotations", [])

if labels:
    for i, label in enumerate(labels, 1):
        name       = label["description"]
        confidence = label["score"] * 100
        
        if confidence > 90:
            emoji = "🟢"  #  sure
        elif confidence > 70:
            emoji = "🟡"  # somehow sure
        else:
            emoji = "🔴"  # not sure
            
        print(f"  {i}. {emoji} {name}: {confidence:.1f}%")
else:
    print("  No label found")

# --- OBJECTS  ---
print("\n📍 DETECTED OBJECTS (With Location):")
print("-" * 40)

objects = api_response.get("localizedObjectAnnotations", [])

if objects:
    for obj in objects:
        name       = obj["name"]
        confidence = obj["score"] * 100
        print(f"  → {name}: {confidence:.1f}% sure")
else:
    print("  No object location found")

# --- SAFE SEARCH ---
print("\n SAFE SEARCH CHECK:")
print("-" * 40)

safe_search = api_response.get("safeSearchAnnotation", {})

if safe_search:
    checks = {
        "adult":    safe_search.get("adult", "UNKNOWN"),
        "violence": safe_search.get("violence", "UNKNOWN"),
        "racy":     safe_search.get("racy", "UNKNOWN")
    }
    
    for check_name, value in checks.items():
        if value in ["VERY_UNLIKELY", "UNLIKELY"]:
            status = "✅ Safe"
        elif value == "POSSIBLE":
            status = "⚠️  Possible"
        else:
            status = "🚨 Detected!"
            
        print(f"  {check_name.capitalize()}: {status} ({value})")

print("\n" + "="*50)
print("🎉 Test complete! API is working perfectly!")
print("="*50)
