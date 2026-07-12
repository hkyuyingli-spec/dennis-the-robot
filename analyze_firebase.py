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
import base64
import requests
from fpdf import FPDF, XPos, YPos
from pypdf import PdfWriter
import schedule
import time
import logging
import argparse

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
GMAIL_USER = os.getenv("GMAIL_USER")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RECIPIENT_EMAIL = "hkyuyingli@gmail.com"
current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

# --- LOGGER ---
logging.basicConfig(filename='email_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- INITIALIZE FIREBASE ---
def init_firebase():
    """Initializes Firebase Firestore connection."""
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        logging.error(i18n.translate('error_service_account_not_found', current_lang).format(path=SERVICE_ACCOUNT_PATH))
        return None
    
    try:
        # Check if already initialized to avoid error
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        logging.error(i18n.translate('firebase_initialization_error', current_lang).format(error=e))
        return None

# --- FETCH DATA ---
def fetch_collections(db):
    """Fetches all documents from the required collections."""
    data = {"users": [], "logs": [], "metrics": []}
    try:
        # Fetch Collections
        for col_name, key in [("users", "users"), ("nutribot_logs", "logs"), ("nutribot_metrics", "metrics")]:
            docs = db.collection(col_name).stream()
            if col_name == "nutribot_logs":
                docs = [doc for doc in docs if not doc.to_dict().get("test_run", False)]
            for doc in docs:
                d = doc.to_dict()
                d['id'] = doc.id
                data[key].append(d)
    except Exception as e:
        logging.error(i18n.translate('error_fetching_data', current_lang).format(error=e))
    return data

# --- GENERATE INSIGHTS ---
def process_data(data):
    """Processes raw Firebase data into insights."""
    # Extract unique users from nutribot_metrics
    metrics_users = []
    metrics_profiles = [m for m in data.get("metrics", []) if m.get("event_type") == "user_profile"]
    if metrics_profiles:
        def get_ts(profile):
            ts = profile.get("timestamp")
            if ts:
                if hasattr(ts, "replace"):
                    return ts.replace(tzinfo=None)
                try:
                    return datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            return datetime.min
        
        metrics_profiles.sort(key=get_ts)
        
        # Deduplicate by session_id, keeping the latest one
        session_to_profile = {}
        for p in metrics_profiles:
            sid = p.get("session_id")
            if sid:
                session_to_profile[sid] = p
        
        metrics_users = list(session_to_profile.values())
        
    # Combine with any actual users from the users collection
    combined_users = []
    seen_sessions = set()
    
    # Process users from users collection
    for u in data.get("users", []):
        if u.get("id") == "users" and not u.get("session_id"):
            continue
        sid = u.get("session_id") or u.get("id")
        if sid:
            seen_sessions.add(sid)
            combined_users.append(u)
            
    # Add from metrics
    for u in metrics_users:
        sid = u.get("session_id")
        if sid not in seen_sessions:
            seen_sessions.add(sid)
            combined_users.append(u)
            
    users = combined_users
    data["users"] = users  # Overwrite data["users"] so Excel/sheets get populated
    
    logs = data["logs"]
    total_users = len(users)
    one_week_ago = datetime.now() - timedelta(days=7)
    new_users_count = 0
    
    # Process New Users
    for u in users:
        ts = u.get('created_at') or u.get('timestamp')
        if ts:
            if hasattr(ts, "replace"):
                ts_unaware = ts.replace(tzinfo=None)
            else:
                try:
                    ts_unaware = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts_unaware = datetime.min
            if ts_unaware > one_week_ago:
                new_users_count += 1
                
    # Process Health Goals
    goals_list = []
    for u in users:
        goal = u.get('health_goals') or u.get('health goals') or u.get('goal')
        if goal and goal != "not selected":
            if isinstance(goal, list):
                goals_list.extend(goal)
            else:
                goals_list.append(str(goal))
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
    """Generates or appends to a multi-sheet Excel report."""
    month_str = datetime.now().strftime('%Y-%m')
    filename = f"analytics_report_{month_str}.xlsx"

    def remove_timezone(df):
        """Helper to make datetimes timezone-unaware for Excel."""
        if df.empty:
            return df
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    df[col] = df[col].dt.tz_localize(None)
                except Exception:
                    try:
                        df[col] = df[col].dt.tz_convert(None)
                    except Exception:
                        pass
        return df

    # Prepare current dataframes
    new_summary_df = pd.DataFrame([insights]).drop(columns=['popular_health_goals', 'common_questions', 'category_counts'], errors='ignore')
    new_users_df = remove_timezone(pd.DataFrame(data["users"]))
    new_logs_df = remove_timezone(pd.DataFrame(data["logs"]))
    new_goals_df = pd.DataFrame(list(insights['popular_health_goals'].items()), columns=['Goal', 'Count'])

    if os.path.exists(filename):
        try:
            # Read existing sheets
            existing_sheets = pd.read_excel(filename, sheet_name=None)
            
            # Append Summary
            if "Summary" in existing_sheets:
                summary_df = pd.concat([existing_sheets["Summary"], new_summary_df], ignore_index=True)
            else:
                summary_df = new_summary_df
                
            # Append Users and deduplicate by 'id'
            if "Users" in existing_sheets:
                users_df = pd.concat([existing_sheets["Users"], new_users_df], ignore_index=True)
                if not users_df.empty and 'id' in users_df.columns:
                    users_df = users_df.drop_duplicates(subset=['id'], keep='last').reset_index(drop=True)
            else:
                users_df = new_users_df
                
            # Append Logs and deduplicate by 'id'
            if "Question Logs" in existing_sheets:
                logs_df = pd.concat([existing_sheets["Question Logs"], new_logs_df], ignore_index=True)
                if not logs_df.empty and 'id' in logs_df.columns:
                    logs_df = logs_df.drop_duplicates(subset=['id'], keep='last').reset_index(drop=True)
            else:
                logs_df = new_logs_df
                
            # Popular Topics is updated with the latest monthly aggregated totals
            goals_df = new_goals_df
            
        except Exception as e:
            logging.error(f"Error reading existing Excel file {filename}: {e}. Overwriting instead.")
            summary_df = new_summary_df
            users_df = new_users_df
            logs_df = new_logs_df
            goals_df = new_goals_df
    else:
        summary_df = new_summary_df
        users_df = new_users_df
        logs_df = new_logs_df
        goals_df = new_goals_df

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        users_df.to_excel(writer, sheet_name="Users", index=False)
        logs_df.to_excel(writer, sheet_name="Question Logs", index=False)
        goals_df.to_excel(writer, sheet_name="Popular Topics", index=False)
        
    logging.info(i18n.translate('exported_analytics_report', current_lang))

# --- GENERATE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'NutriBot Analytics Report', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

def export_pdf(insights, ai_insights):
    """Generates a professional PDF report with charts, appending to the monthly file."""
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
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f"Total Users: {insights['total_users']}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"New Users (Week): {insights['new_users_this_week']}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Avg Questions/User: {insights['average_questions_per_user']}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    # Image
    pdf.image('category_chart.png', x=10, y=None, w=150)
    pdf.ln(10)
    
    # AI Insights
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "AI Insights & Recommendations", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(0, 10, ai_insights.encode('latin-1', 'replace').decode('latin-1'))
    
    month_str = datetime.now().strftime('%Y-%m')
    filename = f"nutribot_report_{month_str}.pdf"
    temp_filename = "nutribot_report_temp.pdf"
    
    pdf.output(temp_filename)
    
    if os.path.exists(filename):
        try:
            merger = PdfWriter()
            merger.append(filename)
            merger.append(temp_filename)
            merger.write(filename)
            merger.close()
            os.remove(temp_filename)
        except Exception as e:
            logging.error(f"Error appending PDF page to {filename}: {e}")
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass
            os.rename(temp_filename, filename)
    else:
        os.rename(temp_filename, filename)
        
    logging.info(i18n.translate('exported_nutribot_report', current_lang))

# --- SEND HTML EMAIL ---
def send_email(insights, ai_insights):
    """Sends a styled HTML email with attachments via Brevo API."""
    if not GMAIL_USER or not BREVO_API_KEY:
        logging.error(i18n.translate('email_skipped_credentials_missing', current_lang))
        return

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

    month_str = datetime.now().strftime('%Y-%m')
    excel_file = f"analytics_report_{month_str}.xlsx"
    pdf_file = f"nutribot_report_{month_str}.pdf"

    # Prepare attachments
    attachments = []
    for filename in [excel_file, pdf_file]:
        try:
            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    content_base64 = base64.b64encode(f.read()).decode('utf-8')
                attachments.append({
                    "name": filename,
                    "content": content_base64
                })
            else:
                logging.warning(f"Attachment file not found: {filename}")
        except Exception as e:
            logging.error(i18n.translate('error_attaching_file', current_lang).format(filename=filename, error=e))

    # Brevo API Payload
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": "NutriBot Analytics",
            "email": GMAIL_USER
        },
        "to": [
            {
                "email": RECIPIENT_EMAIL
            }
        ],
        "subject": f"NutriBot Analytics Report - {datetime.now().strftime('%Y-%m-%d')}",
        "htmlContent": html
    }
    
    if attachments:
        payload["attachment"] = attachments

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201, 202]:
            logging.info(i18n.translate('email_sent_success', current_lang))
        else:
            logging.error(f"Brevo API Error: Status {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Brevo API Connection Error: {e}")

# --- MAIN ---
def main():
    print(i18n.translate('starting_enhanced_analysis', current_lang))
    db = init_firebase()
    if not db: return

    data = fetch_collections(db)
    insights = process_data(data)
    ai_insights = get_ai_analysis(insights)
    
    # Count today's entries
    today = datetime.now().date()
    today_logs_count = sum(1 for log in data['logs'] if isinstance(log.get('timestamp'), datetime) and log['timestamp'].date() == today)
    today_metrics_count = sum(1 for metric in data['metrics'] if isinstance(metric.get('timestamp'), datetime) and metric['timestamp'].date() == today)
    
    print(f"Today's new entries: {today_logs_count} logs, {today_metrics_count} metrics")
    
    export_excel(data, insights)
    export_pdf(insights, ai_insights)
    send_email(insights, ai_insights)
    print(i18n.translate('all_tasks_completed', current_lang))

# --- SCHEDULER ---
schedule.every().day.at("12:00").do(main)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Firebase data and send email report.")
    parser.add_argument("--test", action="store_true", help="Run the analysis immediately without waiting for the schedule.")
    
    args = parser.parse_args()
    
    if args.test:
        main()
    else:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
