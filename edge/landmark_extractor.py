import numpy as np

NOSE_TIP  = 1
CHIN      = 152
LEFT_EAR_IDX  = 234
RIGHT_EAR_IDX = 454

LEFT_EYE  = [159, 145, 33, 133]
RIGHT_EYE = [386, 374, 263, 362]

# iris landmarks (only available with refine_landmarks=True)
LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

def eye_aspect_ratio(landmarks, indices, img_w, img_h):
    points = [(landmarks[i].x * img_w, landmarks[i].y * img_h)
              for i in indices]
    top, bottom, left, right = points
    vertical   = np.linalg.norm(np.array(top)   - np.array(bottom))
    horizontal = np.linalg.norm(np.array(left)  - np.array(right))
    return round(vertical / (horizontal + 1e-6), 4)

def head_pose(landmarks, img_w, img_h):
    nose      = landmarks[NOSE_TIP]
    chin      = landmarks[CHIN]
    left_ear  = landmarks[LEFT_EAR_IDX]
    right_ear = landmarks[RIGHT_EAR_IDX]

    face_center_x = (left_ear.x + right_ear.x) / 2
    face_center_y = (left_ear.y + chin.y) / 2

    yaw   = round((nose.x - face_center_x) * 180, 2)
    pitch = round((nose.y - face_center_y) * 180, 2)

    # roll — tilt of head left/right
    dx = right_ear.x - left_ear.x
    dy = right_ear.y - left_ear.y
    roll = round(np.degrees(np.arctan2(dy, dx)), 2)

    return yaw, pitch, roll

def gaze(landmarks, img_w, img_h):
    def iris_center(indices):
        xs = [landmarks[i].x for i in indices]
        ys = [landmarks[i].y for i in indices]
        return round(sum(xs)/len(xs), 4), round(sum(ys)/len(ys), 4)

    lx, ly = iris_center(LEFT_IRIS)
    rx, ry = iris_center(RIGHT_IRIS)

    # average gaze point (normalized 0-1)
    gaze_x = round((lx + rx) / 2, 4)
    gaze_y = round((ly + ry) / 2, 4)

    # simple zone detection
    if gaze_x < 0.4:
        zone = "left"
    elif gaze_x > 0.6:
        zone = "right"
    elif gaze_y < 0.4:
        zone = "up"
    elif gaze_y > 0.6:
        zone = "down"
    else:
        zone = "center"

    return {
        "iris_left_x":  lx,
        "iris_left_y":  ly,
        "iris_right_x": rx,
        "iris_right_y": ry,
        "gaze_zone":    zone
    }

def extract_all(landmarks, img_w, img_h):
    ear_l = eye_aspect_ratio(landmarks, LEFT_EYE,  img_w, img_h)
    ear_r = eye_aspect_ratio(landmarks, RIGHT_EYE, img_w, img_h)
    yaw, pitch, roll = head_pose(landmarks, img_w, img_h)
    gaze_data = gaze(landmarks, img_w, img_h)

    return {
        "eye": {
            "ear_left":       ear_l,
            "ear_right":      ear_r,
            "ear_avg":        round((ear_l + ear_r) / 2, 4),
            "blink_detected": bool((ear_l + ear_r) / 2 < 0.05)
        },
        "head_pose": {
            "yaw":   yaw,
            "pitch": pitch,
            "roll":  roll
        },
        "gaze": gaze_data
    }