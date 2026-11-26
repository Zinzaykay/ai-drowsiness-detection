import numpy as np
class Feature_Extractor: 
    def get_landmark_points(self,face_landmarks, indices):
        return [
            face_landmarks[i]
            for i in indices
        ]

class Ear(Feature_Extractor) : 
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
    def calculate_ear(self,face_landmarks,RIGHT_OR_LEFT_EYE):
        # Danh sánh lưu tọa độ landmark của mỗi điểm quanh mắt 
        list_landmark_point_of_eye = self.get_landmark_points(face_landmarks, RIGHT_OR_LEFT_EYE)

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


class Mar(Feature_Extractor):
    def __init__(self):
        # index các điểm landmark quanh miệng dùng để tính 
        self.MOUTH = [61, 291, 13, 14]
    def calculate_mar(self,face_landmarks):
        # Lấy tọa độ các landmark
        mouth_points = self.get_landmark_points(
            face_landmarks,
            self.MOUTH
        )

        # Lấy tọa độ (x, y)
        left_corner = np.array([
            mouth_points[0].x,
            mouth_points[0].y
        ])

        right_corner = np.array([
            mouth_points[1].x,
            mouth_points[1].y
        ])

        upper_lip = np.array([
            mouth_points[2].x,
            mouth_points[2].y
        ])

        lower_lip = np.array([
            mouth_points[3].x,
            mouth_points[3].y
        ])

        # Khoảng cách dọc giữa môi trên và môi dưới
        vertical_distance = np.linalg.norm(
            upper_lip - lower_lip
        )

        # Khoảng cách ngang giữa hai khóe miệng
        horizontal_distance = np.linalg.norm(
            left_corner - right_corner
        )

        # MAR
        mar = vertical_distance / horizontal_distance

        return mar
