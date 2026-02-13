# LifeXia Project - Run Instructions

## Prerequisites
- Python 3.8+
- Node.js (Optional, only if you need to run specific frontend tools, but currently served via Flask)

## 1. Environment Setup

It is recommended to use a virtual environment to manage dependencies.

### Create and Activate Virtual Environment

**Mac/Linux:**
```bash
# Create venv if not exists
python3 -m venv .venv

# Activate venv
source .venv/bin/activate
```

**Windows:**
```bash
# Create venv
python -m venv .venv

# Activate venv
.venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r backend/requirements.txt
```

## 2. Configuration
Ensure you have a `.env` file in the root directory with the necessary keys (OpenAI/Gemini/HuggingFace API keys, Database URL, etc.). A `.env.example` is provided.

## 3. Running the Application

To start the Flask backend (which also serves the frontend):

```bash
# Run from the project root directory
python3 -m backend.app
```

The application will start at `http://localhost:5000`.

## 4. WhatsApp QR Code Feature

The "Connect on WhatsApp" feature uses a dynamic QR code generator.

- **How it works:** The QR code is generated instantly using the `api.qrserver.com` API.
- **Customization:** To change the target WhatsApp number:
    1. Open `frontend/templates/index.html`.
    2. Search for `api.qrserver.com`.
    3. Update the phone number in the URL: `data=https://wa.me/919824794027`.
    4. Replace `919824794027` with your desired number (Country Code + Number, no + symbol).

## 5. Map Data
The map loads data from `frontend/static/js/locations.json`.
- To update data, edit `Hospital data (1).xlsx` and use the available conversion tools if necessary.
