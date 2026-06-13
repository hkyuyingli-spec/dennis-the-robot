# NutriBot Analytics

This folder contains the analytics and reporting system for NutriBot.

## Setup Instructions

### 1. Gmail App Password
To allow the script to send emails using your Gmail account, you must set up an **App Password**. A regular password will not work due to Google's security policies.

1. Go to your [Google Account settings](https://myaccount.google.com/).
2. Select **Security**.
3. Under "How you sign in to Google," select **2-Step Verification** and turn it on if it's not already.
4. Search for **App Passwords** in the search bar at the top or find it at the bottom of the 2-Step Verification page.
5. Enter a name (e.g., "NutriBot Analytics") and click **Create**.
6. Copy the 16-character password generated. This is your `GMAIL_PASSWORD`.

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Ensure you have `serviceAccountKey.json` in the root directory.

### 3. Running the Analysis
Run the script using Python:
```bash
python analyze_firebase.py
```

The script will:
- Connect to Firestore.
- Analyze user goals and questions.
- Generate AI insights using Groq.
- Export `analytics_report.csv` and `insights.json`.
- Send a summary email to the designated recipient.
