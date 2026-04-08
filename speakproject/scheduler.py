from apscheduler.schedulers.background import BackgroundScheduler
from .utils import send_session_reminders

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_session_reminders, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler Started⏰")