import requests
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_TTS_KEY    = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION")

print("=" * 50)
print("SAFEROAD AI - Azure TTS Test")
print("=" * 50)

if not AZURE_TTS_KEY:
    print("[ERROR] Azure TTS key not found!")
    exit()

print(f"[OK] TTS Key: {AZURE_TTS_KEY[:8]}...")

# Alert text to convert to speech
alert_text = (
    "Warning! Serious accident detected "
    "on main street. Emergency services "
    "have been notified. Please avoid the area."
)

print(f"[OK] Alert text ready")
print("[..] Sending Request to Azure TTS...")

# Step 1: Access token
token_url = (
    f"https://{AZURE_TTS_REGION}"
    ".api.cognitive.microsoft.com"
    "/sts/v1.0/issueToken"
)

token_headers = {
    "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY
}

try:
    token_response = requests.post(
        token_url,
        headers = token_headers
    )
    access_token = token_response.text
    print("[OK] Got Access token ")

except Exception as e:
    print(f"[ERROR] Token not accessed: {e}")
    exit()

# Step 2: Send Request to TTS
tts_url = (
    f"https://{AZURE_TTS_REGION}"
    ".tts.speech.microsoft.com"
    "/cognitiveservices/v1"
)

tts_headers = {
    "Authorization":  f"Bearer {access_token}",
    "Content-Type":   "application/ssml+xml",
    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
}

# Text to SSML
ssml_text = f"""
<speak version='1.0' xml:lang='en-US'>
    <voice xml:lang='en-US' name='en-US-JennyNeural'>
        {alert_text}
    </voice>
</speak>
"""

try:
    tts_response = requests.post(
        tts_url,
        headers = tts_headers,
        data    = ssml_text.encode("utf-8")
    )

    if tts_response.status_code == 200:
        # Save Audio file
        with open("alert_audio.mp3", "wb") as f:
            f.write(tts_response.content)

        print("[OK] Audio file saved: alert_audio.mp3")

    else:
        print(f"[ERROR] Status: {tts_response.status_code}")
        print(f"        {tts_response.text}")
        exit()

except Exception as e:
    print(f"[ERROR] {e}")
    exit()

print("")
print("=" * 50)
print("[SUCCESS] Azure TTS is working!")
print(f"          Audio saved: alert_audio.mp3")
print("          Open the File and Listen!")
print("=" * 50)
print("")
print("[DONE] AZURE TTS APIs is ready!")
print("=" * 50)