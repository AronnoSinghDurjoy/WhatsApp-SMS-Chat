import sys
import time
import random
import pywhatkit as kit
import oracledb
import pyautogui
import schedule
import pyperclip

from PyQt5 import QtWidgets, QtCore, QtGui


# --------------------- Core Functions ---------------------

def send_whatsapp_message(number, message, log_callback=None):
    """
    Opens WhatsApp Web chat using pywhatkit and sends the message.
    After sending, it logs the forwarded SMS via the provided callback.
    """
    print(f"Opening WhatsApp chat for {number}...")
    kit.sendwhatmsg_instantly(number, "", wait_time=15, tab_close=False)

    additional_wait = random.randint(5, 8)
    time.sleep(additional_wait)
    pyautogui.press("backspace", presses=50, interval=0.1)

    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(random.uniform(1, 2))
    pyautogui.press("enter")

    time.sleep(random.randint(10, 15))
    time.sleep(random.uniform(1, 2))
    pyautogui.hotkey("ctrl", "w")
    time.sleep(random.uniform(1, 2))

    print("Message sent!")
    if log_callback:
        log_callback(f"SMS forwarded to {number}:\n{message}")


def safe_fetch(cursor, query, default_message):
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else default_message
    except Exception as e:
        print(f"Query Error: {e}")
        return default_message


def send_report(phone_numbers, log_callback=None):
    cursor = None
    connection = None
    username = "dwh_user"
    password = "dwh_user_123"
    dsn = "192.168.61.203:1521/dwhdb02"

    try:
        connection = oracledb.connect(user=username, password=password, dsn=dsn)
        cursor = connection.cursor()

        # Date Query
        date_query = "SELECT TO_CHAR(TRUNC(SYSDATE-1), 'YYYY-MM-DD') FROM DUAL"
        report_date = safe_fetch(cursor, date_query, "Date not found")

        # Total Revenue Query
        total_revenue_query = """
            SELECT 'Total Revenue: ' || 
                   REPLACE(TO_CHAR(ROUND(SUM(V41_DEBIT_AMOUNT + G41_DEBIT_AMOUNT + S41_DEBIT_AMOUNT + R41_DEBIT_AMOUNT)), 
                   'FM999,999,999,999'), ',', ',') || ' BDT'
            FROM (
                SELECT 
                    (SELECT SUM(V41_DEBIT_AMOUNT) FROM L3_VOICE 
                     WHERE V387_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                                    WHERE DATE_VALUE = TRUNC(SYSDATE-1))) AS V41_DEBIT_AMOUNT,
                    (SELECT SUM(G41_DEBIT_AMOUNT) FROM L3_DATA 
                     WHERE G383_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                                    WHERE DATE_VALUE = TRUNC(SYSDATE-1))) AS G41_DEBIT_AMOUNT,
                    (SELECT SUM(S41_DEBIT_AMOUNT) FROM L3_SMS 
                     WHERE S387_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                                    WHERE DATE_VALUE = TRUNC(SYSDATE-1))) AS S41_DEBIT_AMOUNT,
                    (SELECT SUM(R41_DEBIT_AMOUNT) FROM L3_RECURRING 
                     WHERE R377_CYCLEBEGINTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                                      WHERE DATE_VALUE = TRUNC(SYSDATE-1))) AS R41_DEBIT_AMOUNT
                FROM DUAL
            )
        """

        voice_revenue_query = """
            SELECT 'Voice Revenue: ' || 
                   REPLACE(TO_CHAR(ROUND(SUM(V41_DEBIT_AMOUNT)), 
                   'FM999,999,999,999'), ',', ',') || ' BDT'
            FROM L3_VOICE
            WHERE V387_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                            WHERE DATE_VALUE = TRUNC(SYSDATE-1))
        """

        data_revenue_query = """
            SELECT 'Data Revenue: ' || 
                   REPLACE(TO_CHAR(ROUND(SUM(G41_DEBIT_AMOUNT)), 
                   'FM999,999,999,999'), ',', ',') || ' BDT'
            FROM L3_DATA
            WHERE G383_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                            WHERE DATE_VALUE = TRUNC(SYSDATE-1))
        """

        sms_revenue_query = """
            SELECT 'SMS Revenue: ' || 
                   REPLACE(TO_CHAR(ROUND(SUM(S41_DEBIT_AMOUNT)), 
                   'FM999,999,999,999'), ',', ',') || ' BDT'
            FROM L3_SMS
            WHERE S387_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                            WHERE DATE_VALUE = TRUNC(SYSDATE-1))
        """

        bundle_revenue_query = """
            SELECT 'Bundle Revenue: ' || 
                   REPLACE(TO_CHAR(ROUND(SUM(R41_DEBIT_AMOUNT)), 
                   'FM999,999,999,999'), ',', ',') || ' BDT'
            FROM L3_RECURRING
            WHERE R377_CYCLEBEGINTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                              WHERE DATE_VALUE = TRUNC(SYSDATE-1))
        """

        data_usage_query = """
            SELECT 'Data Usage: ' || 
                   TO_CHAR(ROUND(SUM(G384_TOTALFLUX)/(1024*1024*1024*1024))) || ' TB'
            FROM L3_DATA
            WHERE G383_CHARGINGTIME_KEY = (SELECT DATE_KEY FROM DATE_DIM 
                                            WHERE DATE_VALUE = TRUNC(SYSDATE-1))
        """

        total_rev = safe_fetch(cursor, total_revenue_query, "Total Revenue: Data not found")
        voice_rev = safe_fetch(cursor, voice_revenue_query, "Voice Revenue: Data not found")
        data_rev = safe_fetch(cursor, data_revenue_query, "Data Revenue: Data not found")
        sms_rev = safe_fetch(cursor, sms_revenue_query, "SMS Revenue: Data not found")
        bundle_rev = safe_fetch(cursor, bundle_revenue_query, "Bundle Revenue: Data not found")
        data_usage = safe_fetch(cursor, data_usage_query, "Data Usage: Data not found")

        message = f"""
Date: {report_date}
-------------------
{total_rev}
{voice_rev}
{data_rev}
{sms_rev}
{bundle_rev}
{data_usage}
        """.strip()

        for number in phone_numbers:
            send_whatsapp_message(number, message, log_callback)

    except oracledb.DatabaseError as e:
        err_msg = f"Database Error: {e}"
        print(err_msg)
        if log_callback:
            log_callback(err_msg)
    except Exception as e:
        err_msg = f"General Error: {e}"
        print(err_msg)
        if log_callback:
            log_callback(err_msg)
    finally:
        if cursor: cursor.close()
        if connection: connection.close()
        if log_callback:
            log_callback("Report sent.")


# --------------------- QThread for Scheduling ---------------------

class ScheduleThread(QtCore.QThread):
    """A separate thread that runs the schedule loop."""
    log_update = QtCore.pyqtSignal(str)

    def __init__(self, phone_numbers, schedule_time):
        super().__init__()
        self.phone_numbers = phone_numbers
        self.schedule_time = schedule_time  # e.g., "13:23"
        self.running = True

    def run(self):
        schedule.clear()
        # Use the schedule time provided by the user.
        schedule.every().day.at(self.schedule_time).do(send_report, self.phone_numbers, self.log_update.emit)
        self.log_update.emit(f"Scheduler set for {self.schedule_time}. Awaiting execution...\n")

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()
        self.log_update.emit("Scheduler stopped.\n")


# --------------------- PyQt5 Main Window ---------------------

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp SMS Chat")
        self.setGeometry(100, 100, 700, 600)
        self.phone_numbers = []
        self.schedule_thread = None

        self.init_ui()

    def init_ui(self):
        # A WhatsApp-stylish color scheme: green accents, visible black fonts, minimalistic design.
        self.setStyleSheet("""
            QWidget {
                background-color: #E5DDD5;  /* WhatsApp chat background */
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #000;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #075E54;  /* Dark WhatsApp green */
                padding: 10px;
            }
            QPushButton {
                background-color: #25D366;  /* WhatsApp green */
                color: #000;
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;  /* Slightly darker on hover */
            }
            QLineEdit, QListWidget, QTextEdit, QTimeEdit {
                background-color: #FFFFFF;
                color: #000;
                border: 1px solid #CCC;
                border-radius: 10px;
                padding: 8px;
            }
            QTextEdit {
                background-color: #F8F8F8;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Label
        title_label = QtWidgets.QLabel("WhatsApp SMS Chat")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Phone Number Entry Layout
        phone_layout = QtWidgets.QHBoxLayout()
        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number (e.g., +123456789)")
        self.add_btn = QtWidgets.QPushButton("Add")
        self.add_btn.clicked.connect(self.add_number)
        self.remove_btn = QtWidgets.QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_number)
        phone_layout.addWidget(self.phone_input)
        phone_layout.addWidget(self.add_btn)
        phone_layout.addWidget(self.remove_btn)
        main_layout.addLayout(phone_layout)

        # List of Phone Numbers
        self.number_list = QtWidgets.QListWidget()
        self.number_list.setFixedHeight(100)
        main_layout.addWidget(self.number_list)

        # Schedule Time Selection Layout
        schedule_layout = QtWidgets.QHBoxLayout()
        schedule_label = QtWidgets.QLabel("Schedule Time (HH:MM):")
        self.time_edit = QtWidgets.QTimeEdit(QtCore.QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.time_edit)
        schedule_layout.addStretch()
        main_layout.addLayout(schedule_layout)

        # Start/Stop Scheduler Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start Scheduler")
        self.start_btn.clicked.connect(self.start_scheduler)
        self.stop_btn = QtWidgets.QPushButton("Stop Scheduler")
        self.stop_btn.clicked.connect(self.stop_scheduler)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        # Log Controls Layout
        log_ctrl_layout = QtWidgets.QHBoxLayout()
        self.clear_log_btn = QtWidgets.QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_ctrl_layout.addStretch()
        log_ctrl_layout.addWidget(self.clear_log_btn)
        main_layout.addLayout(log_ctrl_layout)

        # SMS Log Display
        log_title = QtWidgets.QLabel("SMS Forwarding Log:")
        log_title.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(log_title)
        self.log_area = QtWidgets.QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(200)
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)

    def add_number(self):
        number = self.phone_input.text().strip()
        if number and number not in self.phone_numbers:
            self.phone_numbers.append(number)
            self.number_list.addItem(number)
            self.phone_input.clear()
            self.append_log(f"Added phone number: {number}")
        else:
            self.append_log("Invalid or duplicate phone number.")

    def remove_number(self):
        selected_items = self.number_list.selectedItems()
        if not selected_items:
            self.append_log("No phone number selected for removal.")
            return
        for item in selected_items:
            number = item.text()
            self.phone_numbers.remove(number)
            self.number_list.takeItem(self.number_list.row(item))
            self.append_log(f"Removed phone number: {number}")

    def start_scheduler(self):
        if not self.phone_numbers:
            self.append_log("Please add at least one phone number before starting the scheduler.")
            return
        if not self.schedule_thread or not self.schedule_thread.isRunning():
            schedule_time = self.time_edit.time().toString("HH:mm")
            self.schedule_thread = ScheduleThread(self.phone_numbers, schedule_time)
            self.schedule_thread.log_update.connect(self.append_log)
            self.schedule_thread.start()
            self.append_log(f"Scheduler started for {schedule_time}.")
        else:
            self.append_log("Scheduler is already running.")

    def stop_scheduler(self):
        if self.schedule_thread and self.schedule_thread.isRunning():
            self.schedule_thread.stop()
            self.append_log("Scheduler stopped.")
        else:
            self.append_log("Scheduler is not running.")

    def clear_log(self):
        self.log_area.clear()

    def append_log(self, message):
        timestamp = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.log_area.append(f"[{timestamp}] {message}")


# --------------------- Application Entry Point ---------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
