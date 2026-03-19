# SafeRoad AI
Smart Accident & Hazard Detection System
TIES4911 — University of Jyvaskyla 2026

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/sidrahrahim5-cmyk/saferoad-ai.git
cd saferoad-ai

### 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create .env file
Create a file named .env in the project folder:

GOOGLE_API_KEY=your_key_here
AWS_ACCESS_KEY=your_key_here
AWS_SECRET_KEY=your_key_here
AWS_REGION=us-east-1
AZURE_LANGUAGE_KEY=your_key_here
AZURE_LANGUAGE_ENDPOINT=https://saferoadnlu.cognitiveservices.azure.com/
AZURE_TTS_KEY=your_key_here
AZURE_TTS_REGION=swedencentral

### 5. Run the app
python app.py

### 6. Open browser
http://127.0.0.1:5000