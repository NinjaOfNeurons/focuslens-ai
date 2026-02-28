import cv2
import urllib.parse

# User credentials and camera info
username = 'your-admin-id'
password = 'my-password-'
camera_ip = '192.XXX.0.XXX'
rtsp_port = 554
path = 'avstream/channel=2/stream=0.sdp'

# URL encode username and password
encoded_username = urllib.parse.quote(username)
encoded_password = urllib.parse.quote(password)

# Construct the RTSP URL
rtsp_url = f'rtsp://{encoded_username}:{encoded_password}@{camera_ip}:{rtsp_port}/{path}'

# Open the camera stream using FFmpeg backend
capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not capture.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    ret, frame = capture.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    cv2.imshow("RTSP Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

capture.release()
cv2.destroyAllWindows()
