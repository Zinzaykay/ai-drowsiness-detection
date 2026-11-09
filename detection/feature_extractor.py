import numpy as np
class Ear : 
    def __init__(self) :
        # index của landmark quanh mắt phải và trái , sử dụng cho việc lấy tọa độ landmark 
        self.RIGHT_EYE = [
        33,   # P1 - khóe mắt
        159,  # P2 - phía trên
        158,  # P3 - phía trên
        133,  # P4 - khóe mắt
        145,  # P5 - phía dưới
        144   # P6 - phía dưới
            ]

        self.LEFT_EYE = [
        362,  # P1
        386,  # P2
        385,  # P3
        263,  # P4
        374,  # P5
        373   # P6
            ]

    def get_landmark_points(self,face_landmarks, indices):
        return [
            face_landmarks[i]
            for i in indices
        ]

    def calculate_ear(self,face_landmarks,RIGHT_OR_LEFT_EYE):
        ear = Ear()

        # Danh sánh lưu tọa độ landmark của mỗi điểm quanh mắt 
        list_landmark_point_of_eye = ear.get_landmark_points(face_landmarks, RIGHT_OR_LEFT_EYE)

        # Tính khoảng cách giữa các điểm landmark
        A = np.linalg.norm(
            np.array([list_landmark_point_of_eye[1].x,
                  list_landmark_point_of_eye[1].y]) -
            np.array([list_landmark_point_of_eye[5].x,
                  list_landmark_point_of_eye[5].y])
        )

        B = np.linalg.norm(
            np.array([list_landmark_point_of_eye[2].x,
                  list_landmark_point_of_eye[2].y]) -
            np.array([list_landmark_point_of_eye[4].x,
                  list_landmark_point_of_eye[4].y])
        )

        C = np.linalg.norm(
            np.array([list_landmark_point_of_eye[0].x,
                  list_landmark_point_of_eye[0].y]) -
            np.array([list_landmark_point_of_eye[3].x,
                  list_landmark_point_of_eye[3].y])
        )

        # Công thức EAR
        ear_distance = (A + B) / (2.0 * C)

        return ear_distance
