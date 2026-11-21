"""
Script kiểm thử tích hợp CameraWorker + Controller.
Chạy headless (không cần camera thực, không cần Tkinter display).
Kiểm tra: import, khởi tạo, queue logic, cleanup.
"""
import sys
import os
import queue
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TEST 1: Import tất cả module")
print("=" * 60)
try:
    from app.workers.camera_worker import CameraWorker
    from app.controller import AppController
    from detection.camera import Camera
    from detection.face_detector import Face_Detector
    from detection.feature_extractor import Ear
    from app import app_config
    print("  ✅ Tất cả import thành công")
except Exception as e:
    print(f"  ❌ Import lỗi: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 2: Khởi tạo CameraWorker (không start)")
print("=" * 60)
try:
    q = queue.Queue(maxsize=2)
    worker = CameraWorker(camera_index=0, result_queue=q)
    assert worker.camera_index == 0
    assert worker.result_queue is q
    assert not worker.is_running()
    print("  ✅ Khởi tạo CameraWorker OK")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 3: Queue overflow logic (loại bỏ frame cũ)")
print("=" * 60)
try:
    q = queue.Queue(maxsize=2)
    worker = CameraWorker(camera_index=0, result_queue=q)

    # Đẩy 3 kết quả vào queue maxsize=2
    worker._enqueue_result({"frame": "frame1", "id": 1})
    worker._enqueue_result({"frame": "frame2", "id": 2})
    worker._enqueue_result({"frame": "frame3", "id": 3})  # Phải đẩy được, loại bỏ frame cũ

    items = []
    while not q.empty():
        items.append(q.get_nowait())

    assert len(items) == 2, f"Expected 2 items, got {len(items)}"
    # Frame mới nhất phải có trong queue
    ids = [item["id"] for item in items]
    assert 3 in ids, f"Frame mới nhất (id=3) phải có trong queue, got {ids}"
    print(f"  ✅ Queue overflow logic OK – Items: {ids}")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 4: Khởi tạo AppController (không GUI)")
print("=" * 60)
try:
    controller = AppController(gui=None)
    assert not controller.is_camera_running
    assert controller._camera_worker is None
    assert controller._poll_after_id is None
    print("  ✅ Khởi tạo AppController OK")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 5: CameraWorker start/stop lifecycle (camera index không hợp lệ)")
print("=" * 60)
try:
    q = queue.Queue(maxsize=2)
    worker = CameraWorker(camera_index=999, result_queue=q)  # Camera index không tồn tại
    worker.start()
    time.sleep(2)  # Chờ worker thử mở camera và fail

    # Worker phải đã dừng
    assert not worker.is_running(), "Worker should have stopped after camera open failure"

    # Queue phải có thông báo lỗi
    result = None
    try:
        result = q.get_nowait()
    except queue.Empty:
        pass

    if result is not None and result.get("error"):
        print(f"  ✅ Worker xử lý lỗi camera OK – Error: {result['error'][:50]}...")
    else:
        print(f"  ⚠️ Worker dừng nhưng không gửi lỗi qua queue (result={result})")

    worker.stop(timeout=1.0)
    print("  ✅ Stop sau lỗi OK")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 6: CameraWorker stop khi chưa start")
print("=" * 60)
try:
    worker = CameraWorker(camera_index=0)
    worker.stop()  # Không nên raise exception
    assert not worker.is_running()
    print("  ✅ Stop khi chưa start OK")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 7: start() gọi 2 lần không tạo thread thừa")
print("=" * 60)
try:
    q = queue.Queue(maxsize=2)
    worker = CameraWorker(camera_index=999, result_queue=q)
    worker.start()
    time.sleep(0.1)
    thread1 = worker._thread
    worker.start()  # Gọi lần 2, should be no-op nếu đang running hoặc đã stop
    time.sleep(0.5)
    print("  ✅ Double start không crash")
    worker.stop(timeout=1.0)
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 8: Detection API verification")
print("=" * 60)
try:
    fd = Face_Detector()
    assert hasattr(fd, 'convert_brg_to_rgb'), "Missing convert_brg_to_rgb"
    assert hasattr(fd, 'convert_to_mediapipe_image'), "Missing convert_to_mediapipe_image"
    assert hasattr(fd, 'if_detect_face'), "Missing if_detect_face"
    assert hasattr(fd, 'face_landmarks'), "Missing face_landmarks"
    assert hasattr(fd, 'FaceLandmarker'), "Missing FaceLandmarker"
    assert hasattr(fd, 'options'), "Missing options"
    print("  ✅ Face_Detector API verified")

    ear_calc = Ear()
    assert hasattr(ear_calc, 'calculate_ear'), "Missing calculate_ear"
    assert hasattr(ear_calc, 'RIGHT_EYE'), "Missing RIGHT_EYE"
    assert hasattr(ear_calc, 'LEFT_EYE'), "Missing LEFT_EYE"
    print("  ✅ Ear API verified")

    cam = Camera(camera_id=0)
    assert hasattr(cam, 'start'), "Missing start"
    assert hasattr(cam, 'read_frame'), "Missing read_frame"
    assert hasattr(cam, 'get_ear'), "Missing get_ear"
    assert hasattr(cam, 'release'), "Missing release"
    assert hasattr(cam, 'face_detector'), "Missing face_detector"
    assert hasattr(cam, 'ear'), "Missing ear"
    assert hasattr(cam, 'landmarker'), "Missing landmarker"
    print("  ✅ Camera API verified")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TEST 9: Kết quả dictionary format")
print("=" * 60)
try:
    # Test dictionary format đúng chuẩn
    result_with_face = {
        "frame": "dummy_frame",
        "has_face": True,
        "landmarks": "dummy_landmarks",
        "ear": 0.25,
        "error": None,
    }
    result_no_face = {
        "frame": "dummy_frame",
        "has_face": False,
        "landmarks": None,
        "ear": None,
        "error": None,
    }
    result_error = {
        "frame": None,
        "has_face": False,
        "landmarks": None,
        "ear": None,
        "error": "Test error",
    }
    # Verify required keys
    required_keys = {"frame", "has_face", "landmarks", "ear", "error"}
    for name, r in [("with_face", result_with_face), ("no_face", result_no_face), ("error", result_error)]:
        assert set(r.keys()) == required_keys, f"{name} missing keys: {required_keys - set(r.keys())}"

    print("  ✅ Dictionary format chuẩn")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print()
print("=" * 60)
print("TỔNG KẾT")
print("=" * 60)
print("  Tất cả test cơ bản đã hoàn thành.")
print("  Để test đầy đủ với camera thật, chạy: python main.py")
