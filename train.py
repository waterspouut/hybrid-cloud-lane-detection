from ultralytics import YOLO
import os
from roboflow import Roboflow # Roboflow 라이브러리 추가

# --- [여기서부터] Roboflow에서 복사한 코드 ---
# ⚠️ API Key는 외부에 노출되지 않도록 주의하세요!
rf = Roboflow(api_key="2Os4MSTH57UlwI5dp0Af")
project = rf.workspace("orm-v3brw").project("lane-car-detection-real-63e0w")
version = project.version(2)  # 400장 데이터셋 (업데이트됨)
dataset = version.download("yolov8")
# --- [여기까지] Roboflow 코드 ---


# --- 학습 설정 ---
model_name = 'yolov8n.pt'  # 처음엔 가장 가벼운 nano 모델로 시작
epochs = 100               # 학습 반복 횟수 (100번이면 충분)
imgsz = 640                # 이미지 크기
device = 0                 # GPU 사용 (첫 번째 GPU = 4070 Super)

# 1. 모델 불러오기 (사전 학습된 모델 다운로드)
print(f"🔥 모델 로드 중: {model_name}...")
model = YOLO(model_name)

# 2. 학습 시작!
print(f"🚀 4070 Super로 학습 시작! (Epochs: {epochs})")
# dataset.location이 다운로드된 폴더의 경로를 가지고 있습니다.
results = model.train(
    data=os.path.join(dataset.location, 'data.yaml'),
    epochs=epochs,
    imgsz=imgsz,
    device=device,
    project='runs/train',
    name='exp_v1',
    exist_ok=True,
    val=True  # Validation 활성화: mAP, precision, recall 등 측정
)

# 3. 완료 안내
print("="*50)
print("🎉 학습이 성공적으로 완료되었습니다! 🎉")
# 최종 학습된 가장 좋은 모델 파일 경로 출력
best_model_path = os.path.join('runs/train', 'exp_v1', 'weights', 'best.pt')
print(f"👉 완성된 모델 경로: {best_model_path}")
print("="*50)