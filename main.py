import os
import datetime
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- הגדרות משתנים ---
TELEGRAM_TOKEN ="8917955835:AAEgIOOTErn3UVvhexGv6N8lTsxAT-4D2og"
CALENDAR_ID_A = "f3ade93a27e88897affe2cc50e8ebee8eedc53b8a28d6a3558caf573fb0ae735@group.calendar.google.com"
CALENDAR_ID_B = CALENDAR_ID_A
# חיבור מאובטח ליומן גוגל
SCOPES = ['https://googleapis.com']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=creds)

# פונקציה לבדיקת סטטוס הרכבים כרגע
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    text = "🚗 **מצב הרכבים המשפחתיים כרגע:**\n\n"
    
    for car_name, cal_id in [("רכב א'", CALENDAR_ID_A), ("רכב ב'", CALENDAR_ID_B)]:
        events_result = calendar_service.events().list(
            calendarId=cal_id, timeMin=now, maxResults=1, singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        if not events:
            text += f"🟢 {car_name}: פנוי לחלוטין היום!\n"
        else:
            event = events[0]
            start = event['start'].get('dateTime', event['start'].get('date'))
            time_str = start.split('T')[1][:5] if 'T' in start else "כל היום"
            text += f"🔴 {car_name}: תפוס (אירוע: {event['summary']} בשעה {time_str})\n"
            
    await update.message.reply_text(text, parse_mode="Markdown")

# פונקציה להזמנת רכב
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        car = context.args[0]
        start_time = context.args[1]
        end_time = context.args[2]
        
        cal_id = CALENDAR_ID_A if "א" in car else CALENDAR_ID_B
        today = datetime.date.today().isoformat()
        
        event = {
            'summary': f'הוזמן ע"י {update.message.from_user.first_name}',
            'start': {'dateTime': f'{today}T{start_time}:00', 'timeZone': 'Asia/Jerusalem'},
            'end': {'dateTime': f'{today}T{end_time}:00', 'timeZone': 'Asia/Jerusalem'},
        }
        
        calendar_service.events().insert(calendarId=cal_id, body=event).execute()
        await update.message.reply_text(f"✅ רכב {car} ננעל עבורך בהצלחה בין {start_time} ל-{end_time}!")
    except Exception as e:
        await update.message.reply_text("❌ שגיאה. נא לכתוב: /book [א/ב] [שעת התחלה] [שעת סיום]\nלדוגמה: /book א 14:00 16:00")

def main():
    # תיקון קריטי עבור גרסאות פייתון חדשות בשרתי ענן
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("book", book))
    
    print("הבוט פועל ברקע...")
    application.run_polling()

if __name__ == '__main__':
    main()
