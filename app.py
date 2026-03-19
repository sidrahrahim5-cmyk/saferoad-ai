import base64
import io
import os
import time
from datetime import datetime

import boto3
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from PIL import Image
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"]      = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

GOOGLE_API_KEY          = os.getenv("GOOGLE_API_KEY")
AWS_ACCESS_KEY          = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY          = os.getenv("AWS_SECRET_KEY")
AWS_REGION              = os.getenv("AWS_REGION")
AZURE_LANGUAGE_KEY      = os.getenv("AZURE_LANGUAGE_KEY")
AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")
AZURE_TTS_KEY           = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION        = os.getenv("AZURE_TTS_REGION")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

HAZARD_KEYWORDS = [
    "collision", "accident", "crash",
    "fire", "smoke", "emergency",
    "damaged", "damage", "wreck",
    "smash", "impact", "destruction",
    "bumper", "fender", "broken",
    "debris", "injury", "injured"
]


def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ============================================
# Google Vision API
# ============================================
def analyze_google_vision(image_bytes):
    url = (
        "https://vision.googleapis.com/v1/"
        f"images:annotate?key={GOOGLE_API_KEY}"
    )

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    body = {
        "requests": [{
            "image": {"content": image_b64},
            "features": [
                {"type": "LABEL_DETECTION",     "maxResults": 10},
                {"type": "OBJECT_LOCALIZATION", "maxResults": 5},
                {"type": "SAFE_SEARCH_DETECTION"}
            ]
        }]
    }

    try:
        response = requests.post(url, json=body)
        result   = response.json()

        if "error" in result:
            return None, result["error"]["message"]

        data   = result["responses"][0]
        labels = data.get("labelAnnotations", [])

        detected = [
            {
                "name":  l["description"],
                "score": round(l["score"] * 100, 1)
            }
            for l in labels
        ]

        return {"labels": detected}, None

    except Exception as e:
        return None, str(e)


# ============================================
# AWS Rekognition
# ============================================
def analyze_rekognition(image_bytes):
    try:
        client = boto3.client(
            "rekognition",
            aws_access_key_id     = AWS_ACCESS_KEY,
            aws_secret_access_key = AWS_SECRET_KEY,
            region_name           = AWS_REGION
        )

        img        = Image.open(io.BytesIO(image_bytes))
        img_rgb    = img.convert("RGB")
        buffer     = io.BytesIO()
        img_rgb.save(buffer, format="JPEG", quality=95)
        jpeg_bytes = buffer.getvalue()

        response = client.detect_labels(
            Image         = {"Bytes": jpeg_bytes},
            MaxLabels     = 10,
            MinConfidence = 70
        )

        labels = [
            {
                "name":  l["Name"],
                "score": round(l["Confidence"], 1)
            }
            for l in response["Labels"]
        ]

        return {"labels": labels}, None

    except Exception as e:
        return None, str(e)


# ============================================
# Azure Language NLU
# ============================================
def analyze_azure_nlu(text):
    url = (
        f"{AZURE_LANGUAGE_ENDPOINT}"
        "language/:analyze-text?api-version=2023-04-01"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "kind": "SentimentAnalysis",
        "parameters": {"modelVersion": "latest"},
        "analysisInput": {
            "documents": [{
                "id":       "1",
                "language": "en",
                "text":     text
            }]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        result   = response.json()

        if "error" in result:
            return None, result["error"]["message"]

        doc    = result["results"]["documents"][0]
        scores = doc["confidenceScores"]

        negative = scores["negative"] * 100

        if negative >= 70:
            level = "HIGH"
            color = "red"
        elif negative >= 40:
            level = "MEDIUM"
            color = "orange"
        else:
            level = "LOW"
            color = "green"

        return {
            "sentiment": doc["sentiment"],
            "negative":  round(negative, 1),
            "positive":  round(scores["positive"] * 100, 1),
            "level":     level,
            "color":     color
        }, None

    except Exception as e:
        return None, str(e)


# ============================================
# Azure TTS
# ============================================
def generate_tts_audio(alert_text):
    try:
        token_url = (
            f"https://{AZURE_TTS_REGION}"
            ".api.cognitive.microsoft.com"
            "/sts/v1.0/issueToken"
        )

        token_response = requests.post(
            token_url,
            headers={"Ocp-Apim-Subscription-Key": AZURE_TTS_KEY}
        )
        access_token = token_response.text

        tts_url = (
            f"https://{AZURE_TTS_REGION}"
            ".tts.speech.microsoft.com"
            "/cognitiveservices/v1"
        )

        ssml = f"""<speak version='1.0' xml:lang='en-US'>
            <voice xml:lang='en-US' name='en-US-JennyNeural'>
                <prosody rate='slow'>{alert_text}</prosody>
            </voice>
        </speak>"""

        tts_response = requests.post(
            tts_url,
            headers={
                "Authorization":            f"Bearer {access_token}",
                "Content-Type":             "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
            },
            data=ssml.encode("utf-8")
        )

        if tts_response.status_code == 200:
            filename = f"static/alert_{int(time.time())}.mp3"
            with open(filename, "wb") as f:
                f.write(tts_response.content)
            return filename, None

        return None, f"TTS Error: {tts_response.status_code}"

    except Exception as e:
        return None, str(e)


# ============================================
# Routes
# ============================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    location = request.form.get("location", "Unknown Location")

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only JPG/PNG allowed"}), 400

    image_bytes = file.read()
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results = {
        "location":  location,
        "timestamp": timestamp,
        "google":    None,
        "aws":       None,
        "severity":  None,
        "alert":     None,
        "audio":     None,
        "errors":    []
    }

    # Step 1: Google Vision
    google_data, google_err = analyze_google_vision(image_bytes)
    if google_err:
        results["errors"].append(f"Google: {google_err}")
    else:
        results["google"] = google_data

    # Step 2: AWS Rekognition
    aws_data, aws_err = analyze_rekognition(image_bytes)
    if aws_err:
        results["errors"].append(f"AWS: {aws_err}")
    else:
        results["aws"] = aws_data

    # Step 3: Build incident text
    all_objects = []
    if google_data:
        all_objects += [l["name"] for l in google_data["labels"][:10]]
    if aws_data:
        all_objects += [
            l["name"] for l in aws_data["labels"][:10]
            if l["name"] not in all_objects
        ]

    hazard_found = any(
        keyword in obj.lower()
        for obj in all_objects
        for keyword in HAZARD_KEYWORDS
    )

    if hazard_found:
        incident_text = (
            f"Serious accident and collision detected at {location}. "
            f"Vehicles crashed. Objects: {', '.join(all_objects[:6])}. "
            f"People may be injured. Emergency services needed urgently."
        )
    else:
        incident_text = (
            f"Incident at {location}. "
            f"Detected: {', '.join(all_objects[:6])}. "
            f"Requires attention."
        )

    # Step 4: Azure NLU
    severity_data, nlu_err = analyze_azure_nlu(incident_text)
    if nlu_err:
        results["errors"].append(f"Azure NLU: {nlu_err}")
    else:
        results["severity"] = severity_data

    # Step 5: Azure TTS — both cases
    if severity_data:
        if severity_data["negative"] >= 40:
            alert_text = (
                f"Alert! Incident detected at {location}. "
                f"Objects include {', '.join(all_objects[:3])}. "
                f"Severity level is {severity_data['level']}. "
                f"Emergency services notified. Please avoid the area."
            )
        else:
            alert_text = (
                f"Status update for {location}. "
                f"Road conditions appear normal. "
                f"Detected: {', '.join(all_objects[:3])}. "
                f"No immediate hazards found. "
                f"Drive safely."
            )

        results["alert"] = alert_text

        audio_file, tts_err = generate_tts_audio(alert_text)
        if tts_err:
            results["errors"].append(f"TTS: {tts_err}")
        else:
            results["audio"] = audio_file

    return jsonify(results)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static",  exist_ok=True)
    app.run(debug=True, port=5000)