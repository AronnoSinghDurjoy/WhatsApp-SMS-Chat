import pywhatkit as kit
import oracledb
import pyautogui
import schedule
import time
import random
import pyperclip

def send_whatsapp_message(number, message):
    """Same WhatsApp sending function as before"""
    print(f"Opening WhatsApp chat for {number} using pywhatkit...")
    kit.sendwhatmsg_instantly(number, "", wait_time=15, tab_close=False)
    
    additional_wait = random.randint(5, 8)
    print(f"Waiting an extra {additional_wait} seconds for the chat to load...")
    time.sleep(additional_wait)
    
    pyautogui.press("backspace", presses=50, interval=0.1)
    pyperclip.copy(message)
    print("Pasting message from clipboard...")
    pyautogui.hotkey("ctrl", "v")
    
    send_delay = random.uniform(1, 2)
    time.sleep(send_delay)
    pyautogui.press("enter")
    print("Message sent!")
    
    pre_close_wait = random.randint(10, 15)
    print(f"Waiting {pre_close_wait} seconds before closing the tab...")
    time.sleep(pre_close_wait)
    
    print("Closing the WhatsApp tab...")
    time.sleep(random.uniform(1, 2))
    pyautogui.hotkey("ctrl", "w")
    time.sleep(random.uniform(1, 2))

def send_report():
    cursor = None
    connection = None
    username = "dwh_user"
    password = "dwh_user_123"
    dsn = "192.168.61.203:1521/dwhdb02"
    phone_numbers = ["+8801550155096"]

    try:
        connection = oracledb.connect(user=username, password=password, dsn=dsn)
        print("Connected to Oracle Database!")
        cursor = connection.cursor()

        # Modified query to get last 7 days' total revenue
        query = """
            SELECT 
                TO_CHAR(d.date_value, 'DD-MON-YY') AS report_date,
                NVL(SUM(
                    v.voice_rev + 
                    g.data_rev + 
                    s.sms_rev + 
                    r.bundle_rev
                ), 0) AS total_rev
            FROM date_dim d
            LEFT JOIN (
                SELECT V387_CHARGINGTIME_KEY, SUM(V41_DEBIT_AMOUNT) AS voice_rev
                FROM L3_VOICE
                GROUP BY V387_CHARGINGTIME_KEY
            ) v ON d.date_key = v.V387_CHARGINGTIME_KEY
            LEFT JOIN (
                SELECT G383_CHARGINGTIME_KEY, SUM(G41_DEBIT_AMOUNT) AS data_rev
                FROM L3_DATA
                GROUP BY G383_CHARGINGTIME_KEY
            ) g ON d.date_key = g.G383_CHARGINGTIME_KEY
            LEFT JOIN (
                SELECT S387_CHARGINGTIME_KEY, SUM(S41_DEBIT_AMOUNT) AS sms_rev
                FROM L3_SMS
                GROUP BY S387_CHARGINGTIME_KEY
            ) s ON d.date_key = s.S387_CHARGINGTIME_KEY
            LEFT JOIN (
                SELECT R377_CYCLEBEGINTIME_KEY, SUM(R41_DEBIT_AMOUNT) AS bundle_rev
                FROM L3_RECURRING
                GROUP BY R377_CYCLEBEGINTIME_KEY
            ) r ON d.date_key = r.R377_CYCLEBEGINTIME_KEY
            WHERE d.date_value BETWEEN TRUNC(SYSDATE - 7) AND TRUNC(SYSDATE - 1)
            GROUP BY d.date_value
            ORDER BY d.date_value DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Format message
        message = ["Total Revenue Report -"]
        for date, revenue in results:
            formatted_rev = f"{revenue:,.0f}".replace(',', ',')
            message.append(f"Date: {date}, Total Revenue: {formatted_rev} BDT")
        
        message = "\n".join(message)
        print("\n" + message)

        # Send to all numbers
        for number in phone_numbers:
            send_whatsapp_message(number, message)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("Report sent. Next run scheduled for tomorrow.")

schedule.every().day.at("12:10").do(send_report)
print("Scheduler started. Awaiting execution time...")

while True:
    schedule.run_pending()
    time.sleep(1)