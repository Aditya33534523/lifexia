# 🏥 LifeXia - Intelligent Pharmacy Assistant

LifeXia is a state-of-the-art, AI-powered healthcare ecosystem designed to streamline pharmacy interactions, provide intelligent medical assistance, and offer real-time visualization of medical infrastructure.

![LifeXia Logo](frontend/static/images/Logo.jpg)

## 🌟 Key Features

### 1. 🤖 AI Health Assistant
*   **Intelligent Chat**: Get instant answers about medications, dosages, and drug interactions.
*   **Contextual Awareness**: Maintains chat history for a personalized experience.
*   **Prescription Processing**: Support for uploading and analyzing medical documents.

### 2. 📱 WhatsApp Integration
*   **Omnichannel Support**: Seamlessly transition from web chat to WhatsApp.
*   **QR Code Connectivity**: Instant device pairing via dynamic QR code generation.
*   **Broadcast Alerts**: Admin feature for sending emergency or stocking alerts to decentralized users.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Flask, SQLAlchemy |
| **Frontend** | HTML5, JavaScript, TailwindCSS |
| **Communication** | WhatsApp Business API (via Cloud API) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/lifexia.git
cd lifexia
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OpenAI, WhatsApp, etc.)

# Run the backend
python3 -m backend.app
```

---

## 📂 Project Structure

- `backend/`: Flask application, routes, and services (WhatsApp, Chat).
- `frontend/`: Static assets and traditional HTML templates.
- `data/`: Local database and conversation history.

---

## 🎨 Design Philosophy

LifeXia uses a **"Health Grid"** aesthetic, emphasizing:
- **Glassmorphism**: Translucent panels with high-saturation blur.
- **Micro-Animations**: Smooth transitions and pulse indicators for "live" data.
- **Professional Dark Mode**: Optimized for high-contrast medical information display.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Built with ❤️ by the LifeXia Team.*
