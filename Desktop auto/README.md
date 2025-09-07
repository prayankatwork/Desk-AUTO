# DeskAUTO - Desktop Automation Assistant

## Description
DeskAUTO is a desktop automation application that provides voice assistant and gesture control functionalities. It allows users to interact with their computer using voice commands and hand gestures, enhancing productivity and accessibility. The application features user authentication, voice commands for common tasks, weather updates, and gesture-based mouse control.

## Features
- **User Authentication**: Secure login and registration system using SQLite database.
- **Voice Assistant**:
  - Open applications (Notepad, Chrome).
  - Search Google for queries.
  - Get current weather information based on location.
  - Report current time.
  - System control (shutdown, restart, log off).
  - Continuous or single-command listening modes.
- **Gesture Control**: Use hand gestures via webcam to control mouse pointer and perform clicks.
- **GUI**: Modern interface built with CustomTkinter.
- **Real-time Feedback**: Display for voice command responses.

## Requirements
- Python 3.x
- Webcam and microphone for gesture and voice features.
- Internet connection for weather and location services.

## Installation
1. Clone or download the source code.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python app.py
   ```

## Usage
- Register or login to access the dashboard.
- Click "Voice Assistant" to start voice commands.
- Click "Gesture Control" to enable hand gesture mouse control.
- Toggle "Continuous Listening" for ongoing voice input.

## Dependencies
- customtkinter: For GUI.
- pyttsx3: Text-to-speech.
- pyautogui: GUI automation.
- SpeechRecognition: Voice recognition.
- requests: HTTP requests for weather/location.
- opencv-python: Computer vision for gesture control.
- mediapipe: Hand tracking.

## Notes
- Ensure proper permissions for system commands.
- Webcam and microphone must be accessible.
- Weather data from Open-Meteo API.
- Location data from IP-API.
