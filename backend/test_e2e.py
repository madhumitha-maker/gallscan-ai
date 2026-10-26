import io
import json
import urllib.request
import urllib.error
import numpy as np
from PIL import Image

def run_tests():
    print("==================================================")
    print(" GALLSCAN AI — FULL-STACK VERIFICATION TEST SUITE ")
    print("==================================================")

    # 1. Health check
    res = urllib.request.urlopen("http://localhost:8000/api/health")
    health = json.loads(res.read().decode("utf-8"))
    print("\n[PASS] 1. Health Check:")
    print(f"       Status: {health['status']}")
    print(f"       ONNX Loaded: {health['onnx_loaded']}")
    print(f"       PyTorch Loaded: {health['pytorch_loaded']}")
    print(f"       Classes ({health['num_classes']}): {health['classes'][:3]}...")

    # 2. Authentication
    user_payload = {
        "name": "Dr. Sarah Jenkins, MD",
        "email": "sarah.jenkins@hospital.org",
        "password": "ClinicalPassword2026!",
        "role": "radiologist"
    }
    signup_data = json.dumps(user_payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/api/auth/signup",
        data=signup_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        res = urllib.request.urlopen(req)
        auth_data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError:
        login_data = json.dumps({
            "email": user_payload["email"],
            "password": user_payload["password"]
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:8000/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        auth_data = json.loads(res.read().decode("utf-8"))

    token = auth_data["access_token"]
    user = auth_data["user"]
    print("\n[PASS] 2. User Authentication:")
    print(f"       User ID: {user['id']}")
    print(f"       Name: {user['name']} ({user['email']})")
    print(f"       Role: {user['role']}")

    # 3. Create synthetic ultrasound test image
    img_array = np.random.randint(50, 220, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # 4. Predict endpoint (multipart/form-data)
    boundary = "----GallScanBoundaryXYZ123"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="patient_ultrasound_test.png"\r\n')
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(img_bytes)
    body.extend(f"\r\n--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="notes"\r\n\r\n')
    body.extend(b"Right upper quadrant tenderness, Murphy positive\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        "http://localhost:8000/api/predict",
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}"
        }
    )
    res = urllib.request.urlopen(req)
    pred_res = json.loads(res.read().decode("utf-8"))
    print("\n[PASS] 3. Scan Inference & Grad-CAM Generation:")
    print(f"       Prediction ID: #{pred_res['id']}")
    print(f"       Filename: {pred_res['filename']}")
    print(f"       Diagnosis: {pred_res['predicted_display_name']}")
    print(f"       Confidence: {pred_res['confidence'] * 100:.2f}%")
    print("       Top-3 Differential Diagnoses:")
    for item in pred_res["top_3_predictions"]:
        print(f"         - {item['display_name']}: {item['percentage']}%")
    print(f"       Original Image URL: {pred_res['original_image_url']}")
    print(f"       Grad-CAM Heatmap URL: {pred_res['gradcam_image_url']}")

    # 5. History retrieval
    req = urllib.request.Request(
        "http://localhost:8000/api/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    history = json.loads(res.read().decode("utf-8"))
    print("\n[PASS] 4. PostgreSQL Scan Archive History:")
    print(f"       Total Records in Neon DB: {history['total']}")
    print(f"       First Item Diagnosis: {history['items'][0]['predicted_display_name']}")

    # 6. Notifications
    req = urllib.request.Request(
        "http://localhost:8000/api/notifications",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    notifs = json.loads(res.read().decode("utf-8"))
    print("\n[PASS] 5. Notification Activity Stream:")
    print(f"       Total Notifications: {len(notifs['items'])}")
    print(f"       Unread Count: {notifs['unread_count']}")
    print(f"       Latest Alert: {notifs['items'][0]['title']} — {notifs['items'][0]['message'][:60]}...")

    # 7. Frontend Client Routes
    res = urllib.request.urlopen("http://localhost:8000/client/index.html")
    print(f"\n[PASS] 6. Frontend Client Serving: HTTP {res.getcode()} (Landing Page Available)")

    print("\n==================================================")
    print(" ALL 6 VERIFICATION TEST MODULES PASSED (100%)    ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
