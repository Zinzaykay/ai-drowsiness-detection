import os
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Link tải model chuẩn của MediaPipe Face Landmarker
DATA_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = DATA_DIR / "face_landmarker.task"
# Các chỉ số điểm mốc (Landmarks) của MediaPipe (478 điểm)
LEFT_EYE_IDX = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_IDX = [33, 160, 158, 133, 153, 144]
MOUTH_IDX = [78, 81, 13, 311, 308, 402, 14, 178]  # Khóe miệng & viền môi trong
POSE_IDX = [1, 152, 263, 33, 287, 57]  # Mũi, cằm, 2 đuôi mắt, 2 khóe miệng

# Mô hình đầu 3D tiêu chuẩn để tính Pitch, Yaw, Roll qua solvePnP
MODEL_3D_POINTS = np.array([
    (0.0, 0.0, 0.0),          # Đỉnh mũi (1)
    (0.0, -330.0, -65.0),     # Cằm (152)
    (-225.0, 170.0, -135.0),  # Đuôi mắt trái (263)
    (225.0, 170.0, -135.0),   # Đuôi mắt phải (33)
    (-150.0, -150.0, -125.0), # Khóe miệng trái (287)
    (150.0, -150.0, -125.0)   # Khóe miệng phải (57)
], dtype=np.float64)


def ensure_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model MediaPipe tại: {MODEL_PATH}\n"
            f"Hãy kiểm tra lại tên file .task trong thư mục {DATA_DIR}"
        )

def calc_ear(pts):
    """Tính Eye Aspect Ratio (EAR) từ 6 điểm mắt"""
    v1 = np.linalg.norm(pts[1] - pts[5])
    v2 = np.linalg.norm(pts[2] - pts[4])
    h = np.linalg.norm(pts[0] - pts[3])
    return (v1 + v2) / (2.0 * h + 1e-6)


def calc_mar(pts):
    """Tính (MAR) từ 8 điểm môi trong"""
    v1 = np.linalg.norm(pts[1] - pts[7])
    v2 = np.linalg.norm(pts[2] - pts[6])
    v3 = np.linalg.norm(pts[3] - pts[5])
    h = np.linalg.norm(pts[0] - pts[4])
    return (v1 + v2 + v3) / (3.0 * h + 1e-6)


def calc_head_pose(landmarks, img_w, img_h):
    """Tính góc xoay đầu Pitch (cúi/ngửa), Yaw (quay trái/phải), Roll (nghiêng)"""
    image_2d_points = np.array([
        (landmarks[idx].x * img_w, landmarks[idx].y * img_h) for idx in POSE_IDX
    ], dtype=np.float64)

    focal_length = img_w
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2],
        [0, focal_length, img_h / 2],
        [0, 0, 1]
    ], dtype=np.float64)
    dist_coeffs = np.zeros((4, 1))

    success, rot_vec, _ = cv2.solvePnP(
        MODEL_3D_POINTS, image_2d_points, cam_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    if not success:
        return np.nan, np.nan, np.nan

    rmat, _ = cv2.Rodrigues(rot_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
    pitch, yaw, roll = angles[0], angles[1], angles[2]
    return pitch, yaw, roll


def get_frame_label(ann_rows, current_sec):
    """Đối chiếu timestamp của frame với bảng annotations.csv"""
    if ann_rows.empty:
        return "awake", 0
    matched = ann_rows[(ann_rows["start_sec"] <= current_sec) & (current_sec <= ann_rows["end_sec"])]
    if matched.empty:
        return "awake", 0
    # Nếu có nhiều nhãn trùng nhau, lấy theo thứ tự ưu tiên: head_nod > yawn > eye_closed
    behaviors = set(matched["behavior"])
    for b in ["head_nod", "yawn", "eye_closed"]:
        if b in behaviors:
            return b, 1
    return matched.iloc[0]["behavior"], 1


def process_dataset(video_dir: Path, annotations_csv: Path, output_csv: Path):
    ensure_model()

    ann_df = pd.read_csv(annotations_csv) if annotations_csv.exists() else pd.DataFrame(
        columns=["video_name", "start_sec", "end_sec", "behavior"]
    )

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    video_files = sorted(video_dir.glob("*.mp4"))
    if not video_files:
        print(f"Không tìm thấy video .mp4 nào trong {video_dir}")
        return

    all_rows = []

    with vision.FaceLandmarker.create_from_options(options) as detector:
        for vid_path in tqdm(video_files, desc="Đang trích xuất đặc trưng"):
            vid_name = vid_path.name
            parts = vid_path.stem.split("_")
            dataset_name = parts[0] if len(parts) >= 1 else "UNKNOWN"
            subject_id = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else "UNKNOWN"

            vid_anns = ann_df[ann_df["video_name"] == vid_name]

            cap = cv2.VideoCapture(str(vid_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                current_sec = frame_idx / fps
                behavior, binary_label = get_frame_label(vid_anns, current_sec)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = detector.detect(mp_image)

                if result.face_landmarks:
                    lms = result.face_landmarks[0]
                    h, w, _ = frame.shape
                    coords = np.array([(lm.x * w, lm.y * h) for lm in lms])

                    left_ear = calc_ear(coords[LEFT_EYE_IDX])
                    right_ear = calc_ear(coords[RIGHT_EYE_IDX])
                    ear = (left_ear + right_ear) / 2.0
                    mar = calc_mar(coords[MOUTH_IDX])
                    pitch, yaw, roll = calc_head_pose(lms, w, h)
                    face_detected = 1
                else:
                    ear = mar = pitch = yaw = roll = np.nan
                    face_detected = 0

                all_rows.append({
                    "video_name": vid_name,
                    "dataset": dataset_name,
                    "subject_id": subject_id,
                    "frame_idx": frame_idx,
                    "timestamp_sec": round(current_sec, 3),
                    "face_detected": face_detected,
                    "ear": round(float(ear), 5) if face_detected else np.nan,
                    "mar": round(float(mar), 5) if face_detected else np.nan,
                    "pitch": round(float(pitch), 3) if face_detected else np.nan,
                    "yaw": round(float(yaw), 3) if face_detected else np.nan,
                    "roll": round(float(roll), 3) if face_detected else np.nan,
                    "behavior": behavior,
                    "label": binary_label
                })

                frame_idx += 1

            cap.release()

    out_df = pd.DataFrame(all_rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)

    print(f"\nHoàn tất! Đã lưu {len(out_df):,} frames vào: {output_csv}")
    print(f"Tỷ lệ bắt được mặt: {out_df['face_detected'].mean() * 100:.2f}%")
    print("Phân bố nhãn (0: Awake, 1: Drowsy):")
    print(out_df["label"].value_counts(normalize=True).mul(100).round(2).astype(str) + "%")


if __name__ == "__main__":
    process_dataset(
        video_dir=DATA_DIR / "videos/train",
        annotations_csv=DATA_DIR / "annotations/annotations_train.csv",
        output_csv=DATA_DIR / "features/train_features.csv"
    )
    
    # chạy cho test
    # process_dataset(
    #     video_dir=Path("data/videos/test"),
    #     annotations_csv=Path("annotations/annotations.csv"),
    #     output_csv=Path("data/test_features.csv")
    # )
