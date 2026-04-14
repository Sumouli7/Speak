from apscheduler.schedulers.background import BackgroundScheduler
import atexit

_started = False

def start_scheduler():
    global _started
    if _started:
        return

    from .utils import send_session_reminders
    

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_session_reminders,
        trigger='interval',
        minutes=5,
        id='reminder_job',
        replace_existing=True,
    )
    scheduler.start()
    _started = True
    print("✅ Reminder scheduler started")
    atexit.register(lambda: scheduler.shutdown())
    