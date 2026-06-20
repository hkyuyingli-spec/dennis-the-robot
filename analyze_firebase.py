import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from nutribot import i18n
import firebase_admin
from firebase_admin import credentials, firestore
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RECIPIENT_EMAIL = "hkyuyingli@gmail.com"

# --- INITIALIZE FIREBASE ---
def init_firebase():
    """Initializes Firebase Firestore connection."""
    current_lang = os.getenv('NUTRIBOT_LANG') or 'en'
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(i18n.translate('error_service_account_not_found', current_lang).format(path=SERVICE_ACCOUNT_PATH))
        return None
    
    try:
        # Check if already initialized to avoid error
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(i18n.translate('firebase_initialization_error', current_lang).format(error=e))
        return None

# --- FETCH DATA ---
def fetch_collections(db):
    """Fetches all documents from the required collections."""
    data = {"users": [], "logs": [], "metrics": []}
    try:
        # Fetch Collections
        for col_name, key in [("users", "users"), ("nutribot_logs", "logs"), ("nutribot_metrics", "metrics")]:
            docs = db.collection(col_name).stream()
            for doc in docs:
                d = doc.to_dict()
                d['id'] = doc.id
                data[key].append(d)
    except Exception as e:
        print(i18n.translate('error_fetching_data', current_lang).format(error=e))
    return data

# --- GENERATE INSIGHTS ---
def process_data(data):
    """Processes raw Firebase data into insights."""
    users = data["users"]
    logs = data["logs"]
    
    total_users = len(users)
    one_week_ago = datetime.now() - timedelta(days=7)
    new_users_count = 0
    
    # Process New Users
    for u in users:
        ts = u.get('created_at') or u.get('timestamp')
        if ts and isinstance(ts, datetime) and ts.replace(tzinfo=None) > one_week_ago:
            new_users_count += 1
                
    # Process Health Goals
    goals_list = []
    for u in users:
        goal = u.get('health_goals') or u.get('health goals') or u.get('goal')
        if goal:
            if isinstance(goal, list): goals_list.extend(goal)
            else: goals_list.append(str(goal))
    top_goals = pd.Series(goals_list).value_counts().head(5).to_dict()
    
    # Process Questions & Categories
    questions_list = [l.get('question', '') for l in logs if l.get('question')]
    top_questions = pd.Series(questions_list).value_counts().head(5).to_dict()
    
    categories_list = [l.get('category', 'General') for l in logs if l.get('category')]
    category_counts = pd.Series(categories_list).value_counts().to_dict()
    
    avg_questions = len(logs) / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "new_users_this_week": new_users_count,
        "popular_health_goals": top_goals,
        "common_questions": top_questions,
        "category_counts": category_counts,
        "average_questions_per_user": round(avg_questions, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# --- AI INSIGHTS ---
def get_ai_analysis(summary):
    """Uses Groq API to generate smart recommendations."""
    if not GROQ_API_KEY: return "AI Analysis skipped: GROQ_API_KEY missing."
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"Analyze these NutriBot stats: Users:{summary['total_users']}, New:{summary['new_users_this_week']}, Goals:{summary['popular_health_goals']}, Questions:{summary['common_questions']}. Provide 3-4 actionable insights for a health consultant."
    try:
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        return completion.choices[0].message.content
    except Exception as e: return f"AI Analysis Error: {e}"

# --- EXPORT EXCEL ---
def export_excel(data, insights):
    """Generates a multi-sheet Excel report."""
    def remove_timezone(df):
        """Helper to make datetimes timezone-unaware for Excel."""
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        return df

    with pd.ExcelWriter("analytics_report.xlsx", engine="openpyxl") as writer:
        # Summary Sheet
        summary_df = pd.DataFrame([insights]).drop(columns=['popular_health_goals', 'common_questions', 'category_counts'], errors='ignore')
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        # Users Sheet
        users_df = pd.DataFrame(data["users"])
        remove_timezone(users_df).to_excel(writer, sheet_name="Users", index=False)
        
        # Logs Sheet
        logs_df = pd.DataFrame(data["logs"])
        remove_timezone(logs_df).to_excel(writer, sheet_name="Question Logs", index=False)
        
        # Popular Topics Sheet
        goals_df = pd.DataFrame(list(insights['popular_health_goals'].items()), columns=['Goal', 'Count'])
        goals_df.to_excel(writer, sheet_name="Popular Topics", index=False)
        
    print(i18n.translate('exported_analytics_report', current_lang))

# --- GENERATE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'NutriBot Analytics Report', 0, 1, 'C')
        self.ln(5)

def export_pdf(insights, ai_insights):
    """Generates a professional PDF report with charts."""
    # 1. Create Chart
    plt.figure(figsize=(6, 4))
    cats = list(insights['category_counts'].keys())[:5]
    vals = list(insights['category_counts'].values())[:5]
    plt.bar(cats, vals, color='skyblue')
    plt.title('Top Question Categories')
    plt.ylabel('Frequency')
    plt.savefig('category_chart.png')
    plt.close()

    # 2. Create PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    # Metrics
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f"Total Users: {insights['total_users']}", 0, 1)
    pdf.cell(0, 10, f"New Users (Week): {insights['new_users_this_week']}", 0, 1)
    pdf.cell(0, 10, f"Avg Questions/User: {insights['average_questions_per_user']}", 0, 1)
    pdf.ln(10)
    
    # Image
    pdf.image('category_chart.png', x=10, y=None, w=150)
    pdf.ln(10)
    
    # AI Insights
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "AI Insights & Recommendations", 0, 1)
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(0, 10, ai_insights.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf.output("nutribot_report.pdf")
    print(i18n.translate('exported_nutribot_report', current_lang))

# --- SEND HTML EMAIL ---
def send_email(insights, ai_insights):
    """Sends a styled HTML email with attachments."""
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print(i18n.translate('email_skipped_credentials_missing', current_lang))
        return

    msg = MIMEMultipart()
    msg['From'], msg['To'], msg['Subject'] = GMAIL_USER, RECIPIENT_EMAIL, f"NutriBot Analytics Report - {datetime.now().strftime('%Y-%m-%d')}"

    # HTML Body
    goals_html = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in insights['popular_health_goals'].items()])
    questions_html = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in insights['common_questions'].items()])
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #2e7d32;">NutriBot Performance Summary</h2>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr style="background-color: #f2f2f2;"><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Users</td><td>{insights['total_users']}</td></tr>
            <tr><td>New Users (This Week)</td><td>{insights['new_users_this_week']}</td></tr>
            <tr><td>Avg Questions/User</td><td>{insights['average_questions_per_user']}</td></tr>
        </table>
        
        <h3>Popular Health Goals</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">{goals_html}</table>
        
        <h3>Top Questions Asked</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">{questions_html}</table>
        
        <h3>AI Insights</h3>
        <p style="background-color: #e8f5e9; padding: 10px; border-left: 5px solid #2e7d32;">{ai_insights.replace(chr(10), '<br>')}</p>
        
        <p><i>Please find the detailed Excel and PDF reports attached.</i></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # Attachments
    for filename in ["analytics_report.xlsx", "nutribot_report.pdf"]:
        try:
            with open(filename, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)
        except Exception as e:
            print(i18n.translate('error_attaching_file', current_lang).format(filename=filename, error=e))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(i18n.translate('email_sent_success', current_lang))
    except Exception as e: print(f"SMTP Error: {e}")

# --- MAIN ---
def main():
    print(i18n.translate('starting_enhanced_analysis', current_lang))
    db = init_firebase()
    if not db: return

    data = fetch_collections(db)
    insights = process_data(data)
    ai_insights = get_ai_analysis(insights)
    
    export_excel(data, insights)
    export_pdf(insights, ai_insights)
    send_email(insights, ai_insights)
    print(i18n.translate('all_tasks_completed', current_lang))

if __name__ == "__main__":
    main()
