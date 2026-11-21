Video lấy từ NITYMED, UTA-RLDD, được đặt tên theo cấu trúc: [dataset]_[subject]_[behavior]_[id].mp4
File annotations.csv là gán nhãn cho video
video_name: tên video, đã có tên dataset, tên subject, nhãn
dataset: tên dataset của video
subject_id: id của subject (chủ thể)
start_frame: frame bắt đầu đầu của hành động
end_frame: frame kết thúc của hành động
start_sec: giây bắt đầu của hành động
end_sec: giây kết thúc của hành động
duration_sec: độ dài của hành động
behavior: hành động (yawn, head_nod, eye_closed)
fps: fps của vid (25fps)

file train_features là sử dụng mediapipe xem lại video, đối chiếu với file annotations, từ đó chia ra 2 nhãn 0 (tỉnh táo) và 1 (nhãn eye_closed, head_nod và yawn đưa chung về 1)
file extract_features để tạo ra file train_features.csv

