import numpy as np

NOSE_TIP  = 1
CHIN      = 152
LEFT_EAR  = 234
RIGHT_EAR = 454

def eye_aspect_ratio(landmarks, left_indices, right_indices, img_w, img_h):
    def ear_one_eye(indices):
        points = [(landmarks[i].x * img_w, landmarks[i].y * img_h)
                  for i in indices]
        top, bottom, left, right = points
        vertical   = np.linalg.norm(np.array(top)   - np.array(bottom))
        horizontal = np.linalg.norm(np.array(left)  - np.array(right))
        return vertical / (horizontal + 1e-6)

    ear_l = ear_one_eye(left_indices)
    ear_r = ear_one_eye(right_indices)
    return round((ear_l + ear_r) / 2, 4)

def head_pose(landmarks, img_w, img_h):
    nose      = landmarks[NOSE_TIP]
    chin      = landmarks[CHIN]
    left_ear  = landmarks[LEFT_EAR]
    right_ear = landmarks[RIGHT_EAR]

    face_center_x = (left_ear.x + right_ear.x) / 2
    face_center_y = (left_ear.y + chin.y) / 2

    yaw   = round((nose.x - face_center_x) * 180, 2)
    pitch = round((nose.y - face_center_y) * 180, 2)
    return yaw, pitch