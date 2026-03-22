import cv2
import mediapipe as mp

mp_drawing        = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh      = mp.solutions.face_mesh

def draw_landmarks(frame, results):
    mp_drawing.draw_landmarks(
        image=frame,
        landmark_list=results.multi_face_landmarks[0],
        connections=mp_face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_tesselation_style()
    )
    mp_drawing.draw_landmarks(
        image=frame,
        landmark_list=results.multi_face_landmarks[0],
        connections=mp_face_mesh.FACEMESH_IRISES,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_iris_connections_style()
    )
    return frame

def draw_overlay(frame, ear, yaw, pitch, focused):
    h, w = frame.shape[:2]
    color = (0, 255, 0) if focused else (0, 0, 255)
    label = "FOCUSED" if focused else "DISTRACTED"

    cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
    cv2.putText(frame, label, (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 2)
    cv2.putText(frame, f"EAR: {ear:.3f}  Yaw: {yaw:+.1f}  Pitch: {pitch:+.1f}",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, 3)
    return frame