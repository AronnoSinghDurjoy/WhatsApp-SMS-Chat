# ----------------------------------------------------------------------
# Copyright (c) 2023 Aronno Singh
# ----------------------------------------------------------------------
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
    """Sends WhatsApp message with enhanced validation and error handling"""
    if not number.startswith('+88') or len(number) != 14 or not number[3:].isdigit():
        error_msg = f"Invalid number format: {number}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
        return

    try:
        kit.sendwhatmsg_instantly(number, "", wait_time=15, tab_close=False)
        additional_wait = random.randint(5, 8)
        time.sleep(additional_wait)
        pyautogui.press("backspace", presses=50, interval=0.1)
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(random.uniform(1, 2))
        pyautogui.press("enter")
        time.sleep(random.randint(10, 15))
        pyautogui.hotkey("ctrl", "w")

        success_msg = f"Message sent to {number}:\n{message}"
        if log_callback:
            log_callback(success_msg)
        else:
            print(success_msg)
    except Exception as e:
        error_msg = f"Message failed for {number}: {str(e)}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)


def send_report(phone_numbers, log_callback=None):
    query = """
        SELECT 
            TO_CHAR(d.date_value, 'DD-MON-YYYY') AS report_date,
            TO_CHAR(NVL(SUM(
                NVL(v.voice_rev, 0) + 
                NVL(g.data_rev, 0) + 
                NVL(s.sms_rev, 0) + 
                NVL(r.bundle_rev, 0)
            ), 0), 'FM999,999,999,999') || ' BDT' AS total_rev
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

    connection = None
    cursor = None
    try:
        connection = oracledb.connect(
            user="dwh_user",
            password="dwh_user_123",
            dsn="192.168.61.203:1521/dwhdb02"
        )
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        message = "Revenue Report (Last 7 Days):\n"
        message += "-----------------------------\n"
        for row in results:
            message += f"Date: {row[0]}\nTotal Revenue: {row[1]}\n\n"

        if not results:
            message = "No revenue data found for the last 7 days"

        for number in phone_numbers:
            send_whatsapp_message(number, message.strip(), log_callback)

    except oracledb.DatabaseError as e:
        error_msg = f"Database Error: {e}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
    except Exception as e:
        error_msg = f"Unexpected Error: {e}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# --------------------- QThread for Scheduling ---------------------
class ScheduleThread(QtCore.QThread):
    log_update = QtCore.pyqtSignal(str)

    def __init__(self, phone_numbers, schedule_time):
        super().__init__()
        self.phone_numbers = phone_numbers
        self.schedule_time = schedule_time
        self.running = True

    def run(self):
        schedule.clear()
        schedule.every().day.at(self.schedule_time).do(
            send_report,
            self.phone_numbers,
            self.log_update.emit
        )
        self.log_update.emit(f"Scheduler set for {self.schedule_time}")

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()
        self.log_update.emit("Scheduler stopped")


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
        self.setStyleSheet("""
            QWidget {
                background-color: #E5DDD5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #000;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #075E54;
                padding: 10px;
            }
            QPushButton {
                background-color: #25D366;
                color: #000;
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
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

        # Title and Signature
        title_label = QtWidgets.QLabel("WhatsApp SMS Chat")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(QtCore.Qt.AlignCenter)

        signature_label = QtWidgets.QLabel(
            "Developed by Arnop Singh Aronno\n"
            "© 2025 All Rights Reserved"
        )
        signature_label.setAlignment(QtCore.Qt.AlignCenter)
        signature_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                margin-bottom: 20px;
                font-style: italic;
            }
        """)

        # Phone input section
        phone_layout = QtWidgets.QHBoxLayout()
        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Enter number (e.g., 01712345678)")
        self.add_btn = QtWidgets.QPushButton("Add")
        self.add_btn.clicked.connect(self.add_number)
        self.remove_btn = QtWidgets.QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_number)

        # Schedule section
        schedule_layout = QtWidgets.QHBoxLayout()
        schedule_label = QtWidgets.QLabel("Schedule Time (HH:MM):")
        self.time_edit = QtWidgets.QTimeEdit(QtCore.QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")

        # Control buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start Scheduler")
        self.start_btn.clicked.connect(self.start_scheduler)
        self.stop_btn = QtWidgets.QPushButton("Stop Scheduler")
        self.stop_btn.clicked.connect(self.stop_scheduler)

        # Log controls
        log_ctrl_layout = QtWidgets.QHBoxLayout()
        self.clear_log_btn = QtWidgets.QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)

        # Log display
        log_title = QtWidgets.QLabel("SMS Forwarding Log:")
        log_title.setStyleSheet("font-weight: bold;")
        self.log_area = QtWidgets.QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(200)

        # Build layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(signature_label)
        main_layout.addLayout(phone_layout)
        phone_layout.addWidget(self.phone_input)
        phone_layout.addWidget(self.add_btn)
        phone_layout.addWidget(self.remove_btn)
        self.number_list = QtWidgets.QListWidget()
        self.number_list.setFixedHeight(100)
        main_layout.addWidget(self.number_list)
        main_layout.addLayout(schedule_layout)
        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.time_edit)
        schedule_layout.addStretch()
        main_layout.addLayout(btn_layout)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(log_ctrl_layout)
        log_ctrl_layout.addStretch()
        log_ctrl_layout.addWidget(self.clear_log_btn)
        main_layout.addWidget(log_title)
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)

    def add_number(self):
        input_number = self.phone_input.text().strip()

        # Process and validate number
        cleaned = ''.join(filter(str.isdigit, input_number))
        if len(cleaned) < 11:
            self.append_log("Error: Number must have at least 11 digits")
            return

        number_part = cleaned[-11:]
        formatted_number = f"+88{number_part}"

        if len(formatted_number) != 14:
            self.append_log("Error: Invalid number format after processing")
            return

        if formatted_number in self.phone_numbers:
            self.append_log("Error: Duplicate number")
            return

        self.phone_numbers.append(formatted_number)
        self.number_list.addItem(formatted_number)
        self.phone_input.clear()
        self.append_log(f"Added: {formatted_number}")

    def remove_number(self):
        selected = self.number_list.selectedItems()
        if not selected:
            self.append_log("Error: No number selected")
            return

        for item in selected:
            number = item.text()
            self.phone_numbers.remove(number)
            self.number_list.takeItem(self.number_list.row(item))
            self.append_log(f"Removed: {number}")

    def start_scheduler(self):
        if not self.phone_numbers:
            self.append_log("Error: No numbers added")
            return

        if self.schedule_thread and self.schedule_thread.isRunning():
            self.append_log("Error: Scheduler already running")
            return

        schedule_time = self.time_edit.time().toString("HH:mm")
        self.schedule_thread = ScheduleThread(self.phone_numbers, schedule_time)
        self.schedule_thread.log_update.connect(self.append_log)
        self.schedule_thread.start()
        self.append_log(f"Scheduler started for {schedule_time}")

    def stop_scheduler(self):
        if self.schedule_thread and self.schedule_thread.isRunning():
            self.schedule_thread.stop()
            self.append_log("Scheduler stopped")
        else:
            self.append_log("Error: Scheduler not running")

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