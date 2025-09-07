import os
import sqlite3
import pyttsx3
import pyautogui
import speech_recognition as sr
import customtkinter as ctk
import requests
from tkinter import messagebox
from datetime import datetime
import threading
import time
import cv2
import mediapipe as mp
import re

# ===================== DATABASE SETUP =====================
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = cur.fetchone()
    conn.close()
    return result is not None

# ===================== VOICE ASSISTANT =====================
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if data['status'] == 'success':
            return data['lat'], data['lon'], data['city']
        else:
            return None, None, None
    except:
        return None, None, None

def weather_code_to_description(code):
    weather_codes = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "dense freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snow fall",
        73: "moderate snow fall",
        75: "heavy snow fall",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail"
    }
    return weather_codes.get(code, "unknown weather condition")

def get_weather(lat, lon, city):
    if lat is None or lon is None:
        return None
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url)
        data = response.json()
        current_weather = data.get("current_weather", {})
        temp_c = current_weather.get("temperature")
        weather_code = current_weather.get("weathercode")
        weather_desc = weather_code_to_description(weather_code)
        return f"The current weather in {city} is {weather_desc} with a temperature of {temp_c}°C."
    except:
        return None

def listen_and_respond_feedback(feedback_box, stop_event):
    recognizer = sr.Recognizer()
    while not stop_event.is_set():  # Keep listening until stop_event is set
        try:
            with sr.Microphone() as source:
                feedback_box.configure(state="normal")
                feedback_box.delete("0.0", "end")
                feedback_box.insert("end", "Listening...\n")
                feedback_box.configure(state="disabled")
                audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            feedback_box.configure(state="normal")
            feedback_box.insert("end", f"Heard: {command}\n")

            # Normalize command for easier matching
            normalized_command = command.strip()

            # Help command
            if "help" in normalized_command:
                help_text = ("You can say commands like: 'search for cats', 'google weather', "
                             "'open chrome', 'open notepad', 'what time is it', 'what's the weather', or 'stop listening'.")
                speak(help_text)
                feedback_box.insert("end", help_text + "\n")

            # Stop listening command
            elif "stop listening" in normalized_command or "stop" == normalized_command:
                speak("Stopping voice assistant.")
                feedback_box.insert("end", "Voice assistant stopped by user command.\n")
                stop_event.set()
                break

            # Open Notepad
            elif "open notepad" in normalized_command or normalized_command == "notepad":
                os.system("start notepad")
                speak("Opening Notepad")
                feedback_box.insert("end", "Opening Notepad\n")

            # Open Chrome
            elif "open chrome" in normalized_command or normalized_command == "chrome":
                os.system("start chrome")
                speak("Opening Chrome")
                feedback_box.insert("end", "Opening Chrome\n")

            # Weather query
            elif "weather" in normalized_command:
                lat, lon, city = get_location()
                weather_info = get_weather(lat, lon, city)
                if weather_info:
                    speak(weather_info)
                    feedback_box.insert("end", weather_info + "\n")
                else:
                    speak("Sorry, I could not get the weather information.")
                    feedback_box.insert("end", "Weather information not available.\n")

            # Search commands
            elif normalized_command.startswith("search") or "search for" in normalized_command or "google" in normalized_command:
                # Refined regex to detect search queries only
                search_pattern = re.compile(r"^(?:search(?: for)?|google)\s+(.*)$", re.IGNORECASE)
                match = search_pattern.match(normalized_command)
                if match:
                    search_query = match.group(1).strip()
                    if search_query == "":
                        speak("Please say what you want to search for.")
                        feedback_box.insert("end", "No search query detected.\n")
                    else:
                        os.system("start chrome")
                        time.sleep(2)  # Wait for Chrome to open
                        pyautogui.write(search_query)
                        pyautogui.press("enter")
                        speak(f"Searching for {search_query} on Google")
                        feedback_box.insert("end", f"Searching for {search_query} on Google\n")
                else:
                    speak("Please say what you want to search for.")
                    feedback_box.insert("end", "No search query detected.\n")

            # Time query
            elif "time" in normalized_command or "what time" in normalized_command:
                now = datetime.now().strftime("%H:%M:%S")
                speak(f"The time is {now}")
                feedback_box.insert("end", f"Time is {now}\n")

            # System control commands
            elif "shutdown" in normalized_command or "shut down" in normalized_command or "turn off" in normalized_command:
                confirm = messagebox.askyesno("Confirm Shutdown", "Are you sure you want to shut down the PC?")
                if confirm:
                    speak("Shutting down the PC.")
                    os.system("shutdown /s /t 5")
                    feedback_box.insert("end", "System will shutdown in 5 seconds.\n")
                else:
                    speak("Shutdown cancelled.")
                    feedback_box.insert("end", "Shutdown cancelled by user.\n")
            elif "restart" in normalized_command:
                speak("Restarting the PC.")
                os.system("shutdown /r /t 5")
                feedback_box.insert("end", "System will restart in 5 seconds.\n")
            elif "log off" in normalized_command or "logoff" in normalized_command:
                speak("Logging off the PC.")
                os.system("shutdown /l")
                feedback_box.insert("end", "System will log off.\n")

            else:
                speak("I didn't get that. Say 'help' to know what you can say.")
                feedback_box.insert("end", "Unrecognized command.\n")

            feedback_box.configure(state="disabled")
        except Exception as e:
            feedback_box.configure(state="normal")
            speak("Sorry, I could not understand.")
            feedback_box.insert("end", f"Error understanding input: {str(e)}\n")
            feedback_box.configure(state="disabled")

def gesture_control():
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()
    mp_draw = mp.solutions.drawing_utils
    screen_w, screen_h = pyautogui.size()
    last_click_time = 0
    click_cooldown = 0.2
    double_click_window = 0.2
    last_y = None
    click_count = 0
    click_sensitivity = 30  # adjust as needed

    # For smoothing
    smoothing_factor = 0.7
    prev_x, prev_y = 0, 0

    def nothing(x): pass

    cv2.namedWindow("Gesture Control")
    cv2.createTrackbar("Sensitivity", "Gesture Control", click_sensitivity, 100, nothing)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        h, w, _ = frame.shape
        current_time = time.time()

        click_sensitivity = cv2.getTrackbarPos("Sensitivity", "Gesture Control")

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                lm_list = hand_landmarks.landmark
                index_finger = lm_list[8]
                x = int(index_finger.x * screen_w)
                y = int(index_finger.y * screen_h)

                # Smoothing the cursor movement
                smooth_x = prev_x + (x - prev_x) * smoothing_factor
                smooth_y = prev_y + (y - prev_y) * smoothing_factor
                prev_x, prev_y = smooth_x, smooth_y

                pyautogui.moveTo(smooth_x, smooth_y)
                cx, cy = int(index_finger.x * w), int(index_finger.y * h)
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
                cv2.putText(frame, "Pointer", (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                if last_y is not None:
                    dy = last_y - smooth_y
                    if dy > click_sensitivity and current_time - last_click_time > click_cooldown:
                        click_count += 1
                        last_click_time = current_time
                        if click_count == 1:
                            click_type = "Single Click"
                            pyautogui.click()
                        elif click_count == 2:
                            if current_time - last_click_time <= double_click_window:
                                click_type = "Double Click"
                                pyautogui.doubleClick()
                                click_count = 0
                            else:
                                click_count = 1
                                click_type = "Single Click"
                                pyautogui.click()

                        cv2.putText(frame, click_type, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
                last_y = smooth_y
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            click_count = 0

        cv2.imshow("Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# ===================== GUI =====================
class IntelliDeskApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("DeskAUTO")
        self.root.geometry("600x500")
        init_db()
        self.continuous_listening = False  # New state variable for listening mode
        self.stop_event = threading.Event()  # Add stop event to control voice assistant
        self.login_screen()
        self.root.mainloop()

    def login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.root, text="Login to IntelliDesk", font=("Arial", 20)).pack(pady=20)
        self.username_entry = ctk.CTkEntry(self.root, placeholder_text="Username")
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self.root, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        ctk.CTkButton(self.root, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(self.root, text="Register", command=self.register_screen).pack(pady=5)

    def register_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.root, text="Register Account", font=("Arial", 20)).pack(pady=20)
        self.reg_username = ctk.CTkEntry(self.root, placeholder_text="Username")
        self.reg_username.pack(pady=10)
        self.reg_password = ctk.CTkEntry(self.root, placeholder_text="Password", show="*")
        self.reg_password.pack(pady=10)

        ctk.CTkButton(self.root, text="Create Account", command=self.register).pack(pady=10)
        ctk.CTkButton(self.root, text="Back to Login", command=self.login_screen).pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if verify_user(username, password):
            self.dashboard(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()
        if register_user(username, password):
            messagebox.showinfo("Success", "Account created successfully")
            self.login_screen()
        else:
            messagebox.showerror("Error", "Username already exists")

    def dashboard(self, user):
        for widget in self.root.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.root, text=f"Welcome {user}!", font=("Arial", 18)).pack(pady=20)
        self.feedback_box = ctk.CTkTextbox(self.root, width=400, height=100)
        self.feedback_box.pack(pady=10)
        self.feedback_box.insert("end", "Assistant feedback here...\n")
        self.feedback_box.configure(state="disabled")

        ctk.CTkButton(self.root, text="🎙 Voice Assistant", command=self.toggle_voice_assistant).pack(pady=10)
        ctk.CTkButton(self.root, text="🖐 Gesture Control", command=lambda: threading.Thread(target=gesture_control).start()).pack(pady=10)

        # New toggle button for continuous listening mode
        self.continuous_toggle_button = ctk.CTkButton(self.root, text="Enable Continuous Listening", command=self.toggle_continuous_listening)
        self.continuous_toggle_button.pack(pady=10)

    def toggle_voice_assistant(self):
        if not self.stop_event.is_set():  # Start the assistant
            self.stop_event.clear()
            if self.continuous_listening:
                threading.Thread(target=listen_and_respond_feedback, args=(self.feedback_box, self.stop_event), daemon=True).start()
            else:
                # Single command listening mode
                threading.Thread(target=self.listen_once, args=(self.feedback_box,), daemon=True).start()
        else:  # Stop the assistant
            self.stop_event.set()

    def toggle_continuous_listening(self):
        self.continuous_listening = not self.continuous_listening
        if self.continuous_listening:
            self.continuous_toggle_button.configure(text="Disable Continuous Listening")
        else:
            self.continuous_toggle_button.configure(text="Enable Continuous Listening")

    def listen_once(self, feedback_box):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                feedback_box.configure(state="normal")
                feedback_box.delete("0.0", "end")
                feedback_box.insert("end", "Listening once...\n")
                feedback_box.configure(state="disabled")
                audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            feedback_box.configure(state="normal")
            feedback_box.insert("end", f"Heard: {command}\n")

            # Process the command similarly to listen_and_respond_feedback
            if "weather" in command:
                lat, lon, city = get_location()
                weather_info = get_weather(lat, lon, city)
                if weather_info:
                    speak(weather_info)
                    feedback_box.insert("end", weather_info + "\n")
                else:
                    speak("Sorry, I could not get the weather information.")
                    feedback_box.insert("end", "Weather information not available.\n")
            elif "search for" in command or "google" in command or command.strip() == "search":
                if "search for" in command:
                    search_query = command.split("search for",1)[1].strip()
                elif "google" in command:
                    search_query = command.split("google",1)[1].strip()
                elif command.strip() == "search":
                    search_query = ""
                else:
                    search_query = ""
                if search_query:
                    os.system("start chrome")
                    time.sleep(2)
                    pyautogui.write(search_query)
                    pyautogui.press("enter")
                    speak(f"Searching for {search_query} on Google")
                    feedback_box.insert("end", f"Searching for {search_query} on Google\n")
                else:
                    speak("Please say what you want to search for.")
                    feedback_box.insert("end", "No search query detected.\n")
            elif "chrome" in command:
                os.system("start chrome")
                speak("Opening Chrome")
                feedback_box.insert("end", "Opening Chrome\n")
            elif "notepad" in command:
                os.system("start notepad")
                speak("Opening Notepad")
                feedback_box.insert("end", "Opening Notepad\n")
            elif "time" in command:
                now = datetime.now().strftime("%H:%M:%S")
                speak(f"The time is {now}")
                feedback_box.insert("end", f"Time is {now}\n")
            elif "shutdown" in command or "shut down" in command or "turn off" in command:
                confirm = messagebox.askyesno("Confirm Shutdown", "Are you sure you want to shut down the PC?")
                if confirm:
                    speak("Shutting down the PC.")
                    os.system("shutdown /s /t 5")
                    feedback_box.insert("end", "System will shutdown in 5 seconds.\n")
                else:
                    speak("Shutdown cancelled.")
                    feedback_box.insert("end", "Shutdown cancelled by user.\n")
            elif "restart" in command:
                speak("Restarting the PC.")
                os.system("shutdown /r /t 5")
                feedback_box.insert("end", "System will restart in 5 seconds.\n")
            elif "log off" in command or "logoff" in command:
                speak("Logging off the PC.")
                os.system("shutdown /l")
                feedback_box.insert("end", "System will log off.\n")
            else:
                speak("I didn't get that.")
                feedback_box.insert("end", "Unrecognized command.\n")
            feedback_box.configure(state="disabled")
        except Exception as e:
            feedback_box.configure(state="normal")
            speak("Sorry, I could not understand.")
            feedback_box.insert("end", f"Error understanding input: {str(e)}\n")
            feedback_box.configure(state="disabled")

if __name__ == "__main__":
    app = IntelliDeskApp()
