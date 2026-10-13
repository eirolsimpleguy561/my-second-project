import datetime
import time
import sys

def set_alarm():
    while True:
        alarm_time = input("Enter alarm time (HH:MM): ").strip()
        try:
            alarm_hour, alarm_minute = map(int, alarm_time.split(':'))
            if 0 <= alarm_hour <= 23 and 0 <= alarm_minute <= 59:
                return alarm_hour, alarm_minute
            else:
                print("Invalid time! Please use HH:MM format with valid hours and minutes.")
        except ValueError:
            print("Invalid format! Please use HH:MM (e.g., 14:30).")

def countdown(seconds):
    for remaining in range(seconds, 0, -1):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        secs = remaining % 60
        print(f"\rAlarm in: {hours:02d}:{minutes:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 30 + "\r", end="")

def main():
    print("=== Alarm Clock ===")
    alarm_hour, alarm_minute = set_alarm()
    
    now = datetime.datetime.now()
    alarm_datetime = now.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
    
    if alarm_datetime <= now:
        alarm_datetime += datetime.timedelta(days=1)
    
    seconds_until_alarm = (alarm_datetime - now).total_seconds()
    print(f"\nAlarm set for {alarm_hour:02d}:{alarm_minute:02d}")
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    
    countdown(int(seconds_until_alarm))
    
    print("\n⏰ ALARM! ⏰")
    message = input("Enter alarm message: ").strip() or "Time to wake up!"
    print(f"\n{message}")
    
    snooze = input("\nSnooze? (y/n): ").lower()
    if snooze == 'y':
        print("Snoozing for 5 minutes...")
        time.sleep(300)
        print("⏰ SNOOZE ALARM! ⏰")
    else:
        print("Alarm stopped. Have a great day!")

if __name__ == "__main__":
    main()
