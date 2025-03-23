WhatsApp SMS Forwarding Bot
Description
This is a WhatsApp SMS Forwarding Bot built using Python, PyQt5, pywhatkit, and Oracle Database. The application automatically fetches daily revenue and usage data from an Oracle database and forwards it as a WhatsApp message to specified phone numbers. It features a WhatsApp-inspired UI with a stylish green theme, rounded buttons, and a user-friendly interface.

Features
✅ Automated WhatsApp Messaging: Fetches daily reports and forwards them via WhatsApp Web.
✅ WhatsApp-Styled UI: Green-themed, minimalistic chat-like interface.
✅ User-Friendly Design: Easily add/remove phone numbers and set schedule times.
✅ Scheduler Support: Users can schedule reports to be sent at a specific time daily.
✅ Real-Time Log: Displays logs of forwarded messages.
✅ Start/Stop Scheduler: Users can control the scheduling process dynamically.

Technologies Used
PyQt5 (Graphical User Interface)

pywhatkit (WhatsApp automation)

Oracle Database (Data storage & retrieval)

PyAutoGUI & Pyperclip (Automating message sending)

Schedule (Task scheduling for automated forwarding)

How It Works
Fetches data from the Oracle database, including revenue, usage, and other KPIs.

Formats the report into a structured WhatsApp message.

Sends the message to selected phone numbers using WhatsApp Web.

Logs the forwarded SMS in the UI for transparency.

Scheduler runs automatically at a user-defined time
