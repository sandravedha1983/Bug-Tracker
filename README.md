# 🐞 AI Bug Tracker — Enterprise-Grade Issue Management

![Hero Section](file:///C:/Users/sandr/.gemini/antigravity/brain/60fa75db-874d-4678-b2ed-73b15c926bff/final_hero_verification_1772915290591.png)

A high-performance, Flask-based bug tracking platform featuring **AI-driven priority classification**, **Role-Based Access Control (RBAC)**, and **real-time analytics**. Designed for modern engineering teams who value speed, precision, and elegant UX.

---

## ✨ Core Features

### 🧠 AI-Powered Triage
- **Zero-Shot Classification**: Automatically predicts bug priority (High/Medium/Low) based on the textual description using transformer models.
- **Smart Summarization**: Generates concise bug summaries to help developers grasp issues quickly.

### 🔐 Multi-Tier RBAC
- **Admins**: Full platform control, user management, and manual bug assignment.
- **Developers**: Personalized dashboards focusing on assigned tasks and status updates.
- **Testers**: Specialized interface for reporting, tracking, and verifying fixes.

### 📊 Real-Time Analytics
- **Dynamic Dashboards**: Interactive Chart.js visualizations for priority distribution, status overview, and weekly trends.
- **Workload Balancing**: Visualize developer bandwidth to optimize project velocity.

### 📖 Interactive Documentation
- **Swagger/OpenAPI**: Full interactive API documentation at `/apidocs` for seamless backend integration.

### 📬 Automation & Security
- **Email Verification**: Secure signup flow with token-based email confirmation.
- **Role-Based Middleware**: Custom decorators protect sensitive routes and actions.

---

## �️ Visual Gallery

### 🚀 Premium Landing Page
![Hero Section](file:///C:/Users/sandr/.gemini/antigravity/brain/60fa75db-874d-4678-b2ed-73b15c926bff/final_hero_verification_1772915290591.png)

### 🛠️ Core Features & Design
![Features Section](file:///C:/Users/sandr/.gemini/antigravity/brain/60fa75db-874d-4678-b2ed-73b15c926bff/final_features_verification_1772915297431.png)

### 📊 Real-Time Analytics Dashboard
![Analytics Dashboard](file:///C:/Users/sandr/.gemini/antigravity/brain/60fa75db-874d-4678-b2ed-73b15c926bff/final_analytics_verification_1772915304608.png)

---

## �🛠 Tech Stack

- **Backend**: Python 3.x, Flask, SQLAlchemy (ORM)
- **Frontend**: Tailwind CSS, Vanilla JS, Chart.js, AOS Animations
- **AI/ML**: HuggingFace Transformers (MNLI/Zero-shot classification)
- **Database**: SQLite (Development) / PostgreSQL (Production ready)
- **Tools**: Flasgger (Swagger), itsdangerous (Security), Flask-Mail

---

## 📂 Project Structure

The project follows a professional modular architecture:

```text
Bug-Tracker/
├── app/                  # Main application package
│   ├── __init__.py       # App factory & configuration
│   ├── routes.py         # Main blueprint (Auth, Bugs)
│   ├── admin_routes.py   # Platform Admin blueprint
│   ├── analytics_routes.py # Analytics dashboard blueprint
│   ├── models.py         # SQLAlchemy data models
│   ├── ai_utils.py       # AI priority & summary logic
│   ├── email_utils.py    # Email verification & SMTP logic
│   ├── analytics_utils.py # Data processing for charts
│   └── decorators.py      # RBAC & Auth decorators
├── database/             # Persistent storage
│   └── app.db            # SQLite database
├── scripts/              # Utility scripts
│   └── create_admin.py    # Standalone admin account creator
├── static/               # CSS, JS, and Images
├── templates/            # HTML5 (Jinja2) templates
├── .env                  # Environment variables
├── app.py                # Main entry point
├── requirements.txt      # Dependency list
└── README.md             # This file
```

---

## 🚀 Getting Started

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/Bug-Tracker.git
cd Bug-Tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
ADMIN_PASSWORD_HASH=your_admin_pbkdf2_hash
```

### 3. Initialize Admin
```bash
python scripts/create_admin.py
```

### 4. Run Application
```bash
python app.py
```
Access the application at `http://127.0.0.1:5000`.

---

## 🔒 Security Notes
- Password hashing using `werkzeug.security`.
- Protected Admin platform at `/platform-admin` requires session-based authentication.
- URL-safe tokens for email verification with expiration.

---

## 🏗 Future Enhancements
- 🔄 Native GitHub/GitLab integration.
- 📱 Progressive Web App (PWA) support.
- 📈 Advanced ML models for duplicate bug detection.

---
*Created with ❤️ by the AI Bug Tracker Team*
