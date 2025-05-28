# Intrux - Intrusion Detection System with Email & Audio Alerts

**Intrux** is a Python-based intrusion detection system that monitors for intrusions using a webcam and sends **email alerts** with **audio notifications** when a potential intrusion is detected.

## 🚀 Features

- **Intrusion Detection** using OpenCV and other logic.
- **Email Alerts** sent automatically when an intrusion occurs.
- **Audio Notification** (`alert me.wav`) plays upon detection.
- Configurable through environment variables.

## 🧰 Prerequisites

Make sure you have:

- Python 3.6 or higher installed.
- `pip` package manager.
- Webcam support (for real-time detection).
- Access to a valid SMTP-enabled email account.

## 📦 Python Dependencies

Install required packages using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```
## 📁 Project Structure

```bash
intrux/
├── alert me.wav           # Sound played on intrusion
├── intu_detect.py         # Main detection script
├── requirements.txt       # Required Python packages
└── .gitignore             # Ignores .env and other files
```

## ⚙️ Configuration
Step 1: Clone the Repository
```bash
git clone https://github.com/yuva-raj444/intrux.git
cd intrux
```

## Step 2: (Optional) Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```
## Step 3: Create .env File
Create a .env file in the root of the project and configure it like this:
```bash
# Email Configuration
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_email_password_or_app_password
RECEIVER_EMAIL=receiver_email@example.com
SMTP_SERVER=smtp.example.com
SMTP_PORT=587

# File Paths (optional)
ALERT_SOUND_PATH=alert me.wav         # Default: alert me.wav
RECORDING_DIR=recordings              # Default: recordings
CONFIG_FILE=config.json               # Default: config.json
```
## ⚠️ IMPORTANT:

For Gmail, enable 2-Step Verification and use an App Password.

Do NOT share your .env file or email credentials publicly.

Add .env to .gitignore to keep it secure.

## ▶️ How to Run
To start the intrusion detection system:
```bash
python intu detect.py

```

## ✅ Testing
Make sure the .env file is properly configured.

Run the detection script.

Simulate an intrusion (e.g., show a hand or motion to the webcam).

You should hear the alert sound and receive an email notification.


## 📄 License
This project is licensed under the MIT License.


