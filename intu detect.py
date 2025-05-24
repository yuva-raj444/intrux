import cv2
import mediapipe as mp
import numpy as np
import pygame
import threading
from datetime import datetime, time as dt_time
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email configuration loaded from environment variables
EMAIL_CONFIG = {
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),
    'receiver_email': os.getenv('RECEIVER_EMAIL'),
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
}

# File paths from environment variables or defaults
ALERT_SOUND_PATH = os.getenv('ALERT_SOUND_PATH', 'alert me.wav')
RECORDING_DIR = os.getenv('RECORDING_DIR', 'recordings')
CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.json')

# Initialize MediaPipe pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Initialize Pygame mixer for audio alert
pygame.mixer.init()

# Global variables for drawing
drawing = False
start_point = None
end_point = None
zone_points = []

# Global variables for recording
recording = False
out = None

# Default monitoring schedule
monitoring_schedule = {
    'start_time': '08:00',
    'end_time': '23:00',
}

# Recording time and control
RECORD_DURATION = 5  # seconds
record_start_time = None
ready_to_record = True

# Load config and save it to file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return monitoring_schedule

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(monitoring_schedule, f)

def is_monitoring_active():
    current_time = datetime.now().time()
    start = dt_time.fromisoformat(monitoring_schedule['start_time'])
    end = dt_time.fromisoformat(monitoring_schedule['end_time'])
    return start <= current_time <= end

# Play the alert sound
def play_alert():
    pygame.mixer.music.load(ALERT_SOUND_PATH)
    pygame.mixer.music.play()

# Check if the point is within the alert zone
def is_point_in_zone(point, zone_points):
    if len(zone_points) < 2:
        return False
    
    x, y = point
    x1, y1 = zone_points[0]
    x2, y2 = zone_points[1]
    
    return (min(x1, x2) <= x <= max(x1, x2) and 
            min(y1, y2) <= y <= max(y1, y2))

# Mouse callback to draw alert zone
def mouse_callback(event, x, y, flags, param):
    global drawing, start_point, end_point, zone_points
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_point = (x, y)
        zone_points = []
        zone_points.append(start_point)
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_point = (x, y)
            
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_point = (x, y)
        if start_point and end_point:
            zone_points.append(end_point)

def is_point_in_any_zone(point):
    return is_point_in_zone(point, zone_points)

# Start recording video
def start_recording(frame):
    global out, recording, record_start_time, ready_to_record
    if not os.path.exists(RECORDING_DIR):
        os.makedirs(RECORDING_DIR)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{RECORDING_DIR}/intrusion_{timestamp}.avi'
    h, w = frame.shape[:2]
    out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 20.0, (w, h))
    recording = True
    record_start_time = datetime.now()
    ready_to_record = False

# Stop recording and send the email alert
def stop_recording():
    global out, recording, record_start_time, ready_to_record
    if recording and out is not None:
        out.release()
        recording = False
        record_start_time = None
        ready_to_record = True
        # Send the recorded video via email
        latest_video = sorted(
            [f for f in os.listdir(RECORDING_DIR) if f.startswith('intrusion_')],
            reverse=True
        )
        if latest_video:
            video_path = os.path.join(RECORDING_DIR, latest_video[0])
            threading.Thread(target=send_intrusion_alert, args=(video_path,), daemon=True).start()

# Send intrusion alert email
def send_intrusion_alert(video_path):
    global email_status, email_status_time
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['receiver_email']
        msg['Subject'] = f'Intrusion Detected - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        body = "An intrusion has been detected. Please find the attached video recording."
        msg.attach(MIMEText(body, 'plain'))
        
        with open(video_path, 'rb') as f:
            video_attachment = MIMEApplication(f.read(), _subtype='avi')
            video_attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(video_path))
            msg.attach(video_attachment)
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        email_status = "Email Alert Sent Successfully"
        email_status_time = datetime.now()
        print(f"\nAlert email sent successfully to {EMAIL_CONFIG['receiver_email']}")
        return True
    except Exception as e:
        email_status = f"Email Failed: {str(e)}"
        email_status_time = datetime.now()
        print(f"\nFailed to send email: {e}")
        return False

# Main loop
def main():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Security Feed')
    cv2.setMouseCallback('Security Feed', mouse_callback)
    
    alert_triggered = False
    motion_detector = cv2.createBackgroundSubtractorMOG2()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Motion detection
        fgmask = motion_detector.apply(frame)
        motion_detected = np.mean(fgmask) > 10

        # Draw the zone if points are available
        if len(zone_points) == 2:
            cv2.rectangle(frame, zone_points[0], zone_points[1], (0, 0, 255), 2)
            
        # Draw current selection if drawing
        if drawing and start_point and end_point:
            cv2.rectangle(frame, start_point, end_point, (0, 255, 0), 2)

        # MediaPipe pose detection
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        intrusion = False
        if results.pose_landmarks and is_monitoring_active():
            for lm in results.pose_landmarks.landmark:
                x, y = int(lm.x * w), int(lm.y * h)
                if is_point_in_any_zone((x, y)):
                    intrusion = True
                    cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Handle recording
        if intrusion and motion_detected:
            if ready_to_record and not recording:
                start_recording(frame)

        if recording:
            if out is not None:
                out.write(frame)

            elapsed_time = (datetime.now() - record_start_time).total_seconds()
            if elapsed_time >= RECORD_DURATION:
                stop_recording()

        # Display monitoring status
        status = "MONITORING ACTIVE" if is_monitoring_active() else "MONITORING INACTIVE"
        cv2.putText(frame, status, (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                    (0, 255, 0) if is_monitoring_active() else (0, 0, 255), 2)

        # Trigger alert if intrusion detected
        if intrusion and not alert_triggered:
            threading.Thread(target=play_alert, daemon=True).start()
            alert_triggered = True
        elif not intrusion:
            alert_triggered = False

        # Add instructions to the frame
        cv2.putText(frame, "Click and drag to mark alert area", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press ESC to exit", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Security Feed', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    if recording:
        stop_recording()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if not os.path.exists(RECORDING_DIR):
        os.makedirs(RECORDING_DIR)
    monitoring_schedule = load_config()
    main()
