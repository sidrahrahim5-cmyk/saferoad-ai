import boto3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION     = os.getenv("AWS_REGION")

print("=" * 50)
print("SAFEROAD AI - AWS Rekognition Test")
print("=" * 50)

# Check keys
if not AWS_ACCESS_KEY:
    print("[ERROR] AWS keys not found in .env file")
    exit()

print(f"[OK] Access Key: {AWS_ACCESS_KEY[:8]}...")

# Create Rekognition client
try:
    client = boto3.client(
        "rekognition",
        aws_access_key_id     = AWS_ACCESS_KEY,
        aws_secret_access_key = AWS_SECRET_KEY,
        region_name           = AWS_REGION
    )
    print("[OK] AWS Client ready")

except Exception as e:
    print(f"[ERROR] Could not create client: {e}")
    exit()

# Download test image as bytes
TEST_IMAGE_URL = (
    "https://cloud.google.com/static/vision"
    "/docs/images/setagaya_small.jpeg"
)

print("[..] Downloading image...")

try:
    img_data  = requests.get(TEST_IMAGE_URL)
    img_bytes = img_data.content
    print(f"[OK] Image ready: {len(img_bytes)} bytes")

except Exception as e:
    print(f"[ERROR] Image download failed: {e}")
    exit()

# Send image bytes to Rekognition
print("[..] Sending request to Rekognition...")

try:
    response = client.detect_labels(
        Image         = {"Bytes": img_bytes},
        MaxLabels     = 10,
        MinConfidence = 70
    )

except Exception as e:
    print(f"[ERROR] {e}")
    exit()

# Print results
print("")
print("=" * 50)
print("[SUCCESS] AWS Rekognition is working!")
print("=" * 50)

print("")
print("[LABELS] Detected in image:")
print("-" * 40)

for i, label in enumerate(response["Labels"], 1):
    name  = label["Name"]
    score = label["Confidence"]

    if score >= 90:
        lvl = "HIGH  "
    elif score >= 70:
        lvl = "MEDIUM"
    else:
        lvl = "LOW   "

    print(f"  {i:2}. [{lvl}] {name}: {score:.1f}%")

print("")
print("=" * 50)
print("[DONE] Test complete!")
print("=" * 50)