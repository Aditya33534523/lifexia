# 🏥 LIFEXIA - AI-Powered Pharma Healthcare Chatbot

**LIFEXIA** is an intelligent, RAG-based pharmaceutical healthcare chatbot designed to provide **accurate drug information** in emergency situations. Built with patient safety as the top priority, LIFEXIA delivers medication information, dosage guidelines, and safety warnings in a format suitable for both patients and healthcare students.

---

## 🔧 Bugs Fixed (This Update)

### 1. ❌ Chat Not Working on `localhost:5000/` After Sign-In → ✅ FIXED
**Root Cause:** The `index.html` frontend called `/api/chat/message` but `chat_routes.py` only had `/api/chat/query`. These two endpoints were mismatched.

**Fix Applied:**
- Added `/message` endpoint in `chat_routes.py` that handles the full chat flow including WhatsApp forwarding
- Updated `chat.js` to correctly call `/api/chat/message`
- Updated `app.py` to register all blueprints (including `history_bp` and `upload_bp` which were missing)

### 2. ❌ RAG Hallucination on `localhost:5000/chat` → ✅ FIXED
**Root Cause:** When ML dependencies aren't installed (no PyTorch/LangChain), the RAG service returned 503 errors or used the LLM without grounding, causing hallucinated responses.

**Fix Applied:**
- Built a **comprehensive verified drug database** with 15 medications (Paracetamol, Aspirin, Ibuprofen, Amoxicillin, Metformin, Amlodipine, Omeprazole, Cetirizine, Atorvastatin, Epinephrine, Diazepam, Salbutamol, Ciprofloxacin, Losartan, Insulin)
- Database includes **brand-name aliases** (Dolo 650, Crocin, Ecosprin, Brufen, etc.)
- Drug info sourced from **Indian Pharmacopoeia 2022, NLEM 2022, WHO Essential Medicines List**
- **Patient vs Student mode** formatting
- Built-in database is checked FIRST before LLM, preventing hallucination
- Graceful fallback: if a drug isn't found, the system says so honestly instead of guessing

### 3. ❌ WhatsApp Broadcasting Not Working → ✅ FIXED
**Root Cause:** API version mismatch (v21.0 in code vs v22.0 in Meta dashboard)

**Fix Applied:**
- Updated `whatsapp_service.py` to use API `v22.0`
- Improved error extraction from Meta API responses
- Updated `broadcast.js` with proper template handling
- Pre-fills admin WhatsApp number `919824794027`
- Supports both template broadcasts (works anytime) and custom text (24h window)

---

## 🌟 Key Features

### 🤖 RAG-Based Drug Information System
- **Accuracy-First Approach**: Built-in verified drug database checked before LLM
- **15 Medications** with complete pharmacology data
- **40+ Brand Name Aliases** (Dolo, Crocin, Ecosprin, etc.)
- **Patient vs Student Modes**: Different detail levels
  - Patient Mode: Practical usage, safety warnings, when to seek help
  - Student Mode: Technical pharmacology, metabolism, half-life, mechanism
- **Emergency Drug Flagging**: Quick access to critical emergency medications
- **No Hallucination**: System honestly reports when it doesn't have info

### 📱 WhatsApp Business API Integration
- **Template Broadcasting**: Send pre-approved templates to multiple recipients
- **Custom Text Messages**: Send within 24-hour conversation windows
- **Medication Reminders**: Structured reminder messages
- **Emergency Alerts**: Critical health alert broadcasting
- **Hospital Directions**: Send directions via WhatsApp
- **Ayushman/MAA Card Info**: Government health card hospital information

### 🗺️ Health Grid Map
- **Leaflet.js Interactive Map** with facility markers
- **Hospital & Pharmacy Search** with distance calculation
- **Ayushman Bharat Card** hospital filtering
- **MAA Vatsalya Card** support
- **Category Filtering**: Orthopaedic, Gynaecology, Multispeciality, etc.
- **Location-Based**: Auto-detects user GPS position

### 🔐 Authentication
- **Login/Register** system with session management
- **Admin Role**: Admin users see Broadcast button
- **Demo Mode**: Works even when auth backend is down
- **Default Admin**: `admin@lifexia.com` / `admin123`

---

## 📂 Project Structure

```
lifexia/
├── backend/
│   ├── __init__.py
│   ├── app.py                    ← Main Flask application (FIXED)
│   ├── config.py                 ← Environment configuration
│   ├── requirements.txt          ← Python dependencies
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py        ← Login/register endpoints
│   │   ├── chat_routes.py        ← Chat API endpoints (FIXED - added /message)
│   │   ├── history_routes.py     ← Chat history endpoints
│   │   ├── map_routes.py         ← Hospital/pharmacy map API
│   │   ├── upload_routes.py      ← File upload endpoints
│   │   ├── webhook_routes.py     ← WhatsApp webhook handler
│   │   └── whatsapp_routes.py    ← WhatsApp API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_store.py         ← In-memory conversation store
│   │   ├── map_service.py        ← Hospital/pharmacy data service
│   │   ├── rag_service.py        ← RAG + Drug Database (FIXED - no hallucination)
│   │   └── whatsapp_service.py   ← WhatsApp Business API (FIXED - v22.0)
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── frontend/
│   ├── templates/
│   │   ├── index.html            ← Main chat interface
│   │   └── chat.html             ← Alternative chat page
│   └── static/
│       ├── css/
│       │   └── styles.css        ← Glassmorphism UI styles
│       ├── js/
│       │   ├── main.js           ← App initialization (FIXED)
│       │   ├── auth.js           ← Authentication logic (FIXED)
│       │   ├── chat.js           ← Chat functionality (FIXED - correct endpoint)
│       │   ├── broadcast.js      ← WhatsApp broadcast UI (FIXED)
│       │   ├── map.js            ← Health Grid map logic
│       │   └── upload.js         ← File upload handling
│       └── images/
│           └── Logo.jpg
├── data/
│   └── location.json             ← Hospital/pharmacy location data
├── .env.example                  ← Environment template
├── run.sh                        ← Startup script
└── README.md                     ← This file
```

---

## 📡 API Endpoints

### Chat API (`/api/chat/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/init` | Initialize chat session |
| POST | `/api/chat/message` | **Main chat endpoint** (used by index.html) |
| POST | `/api/chat/query` | Alternative query endpoint (used by chat.html) |
| POST | `/api/chat/drug-search` | Direct drug search |
| GET | `/api/chat/emergency-drugs` | List emergency medications |
| GET | `/api/chat/quick-info/<drug>` | Quick drug info |
| GET | `/api/chat/history` | Get session chat history |
| POST | `/api/chat/clear-history` | Clear chat history |

### WhatsApp API (`/api/whatsapp/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/whatsapp/send-message` | Send text message |
| POST | `/api/whatsapp/send-template` | Send template message |
| POST | `/api/whatsapp/broadcast` | **Broadcast to multiple numbers** |
| POST | `/api/whatsapp/medication-reminder` | Send med reminder |
| POST | `/api/whatsapp/emergency-alert` | Send emergency alert |
| POST | `/api/whatsapp/hospital-directions` | Send hospital directions |
| POST | `/api/whatsapp/ayushman-info` | Send Ayushman card info |
| POST | `/api/whatsapp/send-location` | Send location pin |
| GET | `/api/whatsapp/session-status/<phone>` | Check 24h window |

### Map API (`/api/map/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/map/locations` | Get all locations with filtering |

### Auth API (`/api/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/verify` | Verify token |

### History API (`/api/history/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history/<email>` | Get user's chat history |
| GET | `/api/history/conversation/<id>` | Get conversation |
| DELETE | `/api/history/delete/<id>` | Delete conversation |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main chat interface |
| GET | `/chat` | Alternative chat page |
| GET | `/health` | Service health check |

---

## 🚀 Quick Start

### 1. Setup
```bash
python3 -m venv .venv
source .venv/bin/activate   # Mac/Linux
pip install -r backend/requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your WhatsApp credentials
```

### 3. Run
```bash
python -m backend.app
# OR
bash run.sh
```

### 4. Access
- **Main Interface**: http://localhost:5000/
- **Alternative Chat**: http://localhost:5000/chat
- **Health Check**: http://localhost:5000/health

### Default Login
- **Email**: `admin@lifexia.com`
- **Password**: `admin123`

---

## 📱 WhatsApp Configuration

Your WhatsApp Business API credentials (from Meta Developer Console):

| Setting | Value |
|---------|-------|
| App ID | 1226541692966693 |
| Phone Number ID | 100151100304141 4 |
| Business Account ID | 155128022409639 |
| Admin Number | +91 98247 94027 |
| API Version | v22.0 |

### Broadcasting
1. Login as admin (`admin@lifexia.com`)
2. Click the **Broadcast** button in header
3. Select template (e.g., `hello_world`)
4. Enter recipient numbers (comma-separated, with country code)
5. Click **Send Broadcast**

---

## 💊 Supported Drugs (Built-in Verified Database)

| Drug | Category | Emergency |
|------|----------|-----------|
| Paracetamol (Dolo, Crocin, Calpol) | Analgesic/Antipyretic | ✅ |
| Aspirin (Ecosprin, Disprin) | NSAID/Antiplatelet | ✅ |
| Ibuprofen (Brufen, Combiflam) | NSAID | ✅ |
| Amoxicillin (Augmentin, Mox) | Antibiotic | ✅ |
| Metformin (Glycomet, Glucophage) | Antidiabetic | ❌ |
| Amlodipine (Stamlo, Norvasc) | Calcium Channel Blocker | ❌ |
| Omeprazole (Omez, Prilosec) | PPI | ❌ |
| Cetirizine (Zyrtec, Alerid) | Antihistamine | ❌ |
| Atorvastatin (Lipitor, Atorva) | Statin | ❌ |
| Epinephrine (Adrenaline, EpiPen) | Emergency Drug | ✅ |
| Diazepam (Valium, Calmpose) | Benzodiazepine | ✅ |
| Salbutamol (Asthalin, Ventolin) | Bronchodilator | ✅ |
| Ciprofloxacin (Ciplox, Cipro) | Fluoroquinolone | ❌ |
| Losartan (Repace, Cozaar) | ARB | ❌ |
| Insulin (Lantus, NovoRapid, Humulin) | Antidiabetic Hormone | ✅ |

---

## 🔮 Recommended Next Steps

1. **Add more drugs** to the built-in database in `rag_service.py`
2. **Run data ingestion** (`python backend/services/ingest_data.py`) with your PDF drug documents for full RAG
3. **Create custom WhatsApp templates** in Meta Business Manager for branded broadcasts
4. **Deploy to production** with gunicorn + nginx
5. **Add Redis** for session management and user session tracking
6. **Integrate OCR** for prescription image analysis
7. **Add user registration** with database-backed auth

---

*Built with ❤️ for patient safety — LIFEXIA prioritizes accuracy over speed.*
