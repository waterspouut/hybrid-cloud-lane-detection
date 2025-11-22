from flask import Flask
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
from ultralytics import YOLO  # YOLO 임포트 필요
from core.lane_detector import LaneDetector
from core.object_detector import ObjectDetector
import time
import threading
import boto3
from datetime import datetime
import io # 추가: 메모리 상에서 파일 IO 처리를 위해 필요
import csv # 추가: CSV 파일 처리를 위해 필요

app = Flask(__name__)
# cors_allowed_origins='*': 모든 곳에서의 접속 허용
# max_http_buffer_size: 기본 1MB -> 10MB로 증설 (고해상도 이미지 전송 대비)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10*1024*1024)

# --- [설정] ---
# S3 버킷 이름 (본인 버킷 이름으로 꼭 확인!)
S3_BUCKET_NAME = 'lane-data-2025-oreum' 
SAVE_INTERVAL = 3.0  # 3초에 한 번씩만 저장 (데이터 수집용)
LOG_FILE_KEY = 'logs/data.csv' # 추가: 로그 파일 경로

last_save_time = 0   # 마지막으로 저장한 시간 기록용 변수

# --- [초기화] ---
# 감지기 인스턴스 생성
lane_detector = LaneDetector()

# [수정] 커스텀 모델(best.pt) 적용
# 1. 기존 방식대로 일단 생성합니다. (내부적으로 yolov8n.pt가 로드됨)
# object_detector = ObjectDetector(model_size='n') # <-- 기존 코드 주석 처리
object_detector = ObjectDetector(model_size='n') # <-- 그대로 둡니다 (수정X)

# 2. [핵심] 우리가 학습시킨 모델로 덮어씌웁니다!
try:
    print("📦 커스텀 모델(best.pt)로 교체 중...")
    # 주의: best.pt 파일이 app.py와 같은 폴더에 있어야 합니다.
    object_detector.model = YOLO('best.pt') 
    print("✅ 커스텀 모델 교체 완료!")
except Exception as e:
    print(f"⚠️ 커스텀 모델 로드 실패: {e}")
    print("👉 기본 모델(yolov8n.pt)을 사용합니다.")

# boto3 S3 클라이언트 생성 (서버에 설정된 권한 정보 사용)
s3 = boto3.client('s3')


# --- [함수 추가] ---
def upload_to_s3_background(image, filename):
    """
    백그라운드 스레드에서 S3로 이미지를 업로드하는 함수입니다.
    """
    try:
        # 1. OpenCV 이미지(numpy 배열)를 JPG 바이너리 데이터로 인코딩
        # (화질 90% 설정으로 저장 용량 조절)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, buffer = cv2.imencode('.jpg', image, encode_param)
        
        # 2. S3 업로드 수행
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"raw_data/{filename}", # raw_data 폴더 안에 파일을 저장합니다.
            Body=buffer.tobytes(),
            ContentType='image/jpeg'
        )
        print(f"💾 S3 이미지 저장 성공: {filename}")
    except Exception as e:
        print(f"⚠️ S3 이미지 업로드 실패: {e}")

def append_to_s3_log(log_data):
    """
    S3에 있는 CSV 로그 파일에 데이터를 한 줄 추가하는 함수 (추가된 함수)
    """
    try:
        # 1. 기존 로그 파일 읽어오기 (없으면 새로 만듦)
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=LOG_FILE_KEY)
            existing_content = response['Body'].read().decode('utf-8')
        except s3.exceptions.NoSuchKey:
            # 파일이 없으면 헤더(제목줄)를 만듭니다.
            existing_content = "timestamp,filename,car_count,lane_count,processing_time_ms\n"

        # 2. 새로운 데이터 한 줄 만들기 (CSV 형식)
        # timestamp, filename, car_count, lane_count, processing_time_ms
        new_line = f"{log_data['timestamp']},{log_data['filename']},{log_data['car_count']},{log_data['lane_count']},{log_data['processing_time']:.2f}\n"
        
        # 3. 기존 내용에 새 내용 합치기
        new_content = existing_content + new_line

        # 4. S3에 다시 업로드 (덮어쓰기)
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=LOG_FILE_KEY,
            Body=new_content.encode('utf-8'),
            ContentType='text/csv'
        )
        # print(f"📝 S3 로그 추가 완료") # 로그가 너무 많으면 주석 처리

    except Exception as e:
        print(f"⚠️ S3 로그 추가 실패: {e}")


@app.route('/')
def index():
    return "Hybrid Cloud Lane Detection API is Running with S3 Logging!"


@socketio.on('connect')
def handle_connect():
    print("Client connected")


@socketio.on('process_frame')
def handle_frame(data):
    global last_save_time # 전역 변수 사용 선언
    """
    클라이언트(앱)가 'process_frame' 이벤트로 이미지를 보내면 호출됩니다.
    """
    print("1. 📸 이미지 도착! 처리 시작...")
    start_time = time.time()

    # 1. Base64 이미지 디코딩
    try:
        image_data = base64.b64decode(data['image'])
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # [중요] 강제 리사이징 제거! 클라이언트가 보낸 비율 그대로 처리
        # frame = cv2.resize(frame, (640, 480)) 
    except Exception as e:
        print(f"Image decode error: {e}")
        return

    if frame is None:
        return

    # 이미지 크기 확인 (클라이언트 스케일링용)
    height, width = frame.shape[:2]

    # 2. 차선 감지 (좌표 리스트 반환)
    lanes = lane_detector.detect(frame)

    # 3. 객체(자동차) 감지 (좌표 리스트 반환)
    # 현재 object_detector.py 코드는 detect()가 결과를 바로 반환하도록 되어 있음.
    cars = object_detector.detect(frame)

    # 4. 처리 시간 계산
    processing_time = (time.time() - start_time) * 1000  # ms 단위

    # --- [데이터 수집 및 로그 저장 시작] ---
    # 3초마다 한 번씩 저장
    current_time = time.time()
    if current_time - last_save_time > SAVE_INTERVAL:
        last_save_time = current_time
        # 파일명 및 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"

        # 3-1. 이미지 S3 저장 (백그라운드)
        # args=(frame.copy(), ...) : 현재 프레임의 복사본을 넘겨야 안전합니다.
        threading.Thread(target=upload_to_s3_background, args=(frame.copy(), filename)).start()

        # 3-2. 로그 S3 저장 (백그라운드) - 추가된 부분
        log_data = {
            'timestamp': timestamp,
            'filename': filename,
            'car_count': len(cars), # 감지된 차량 수
            'lane_count': len(lanes), # 감지된 차선 수
            'processing_time': processing_time
        }
        threading.Thread(target=append_to_s3_log, args=(log_data,)).start()
    # --- [데이터 수집 및 로그 저장 끝] ---


    # 5. 결과 전송 (JSON 형식 - 모바일 앱에서 그리도록)
    response_data = {
        "lanes": lanes,
        "cars": cars,
        "processing_time": processing_time,
        "image_width": width,   # [추가] 서버가 처리한 이미지 너비
        "image_height": height  # [추가] 서버가 처리한 이미지 높이
    }

    # 요청을 보낸 클라이언트에게 결과 반환 (이벤트명: frame_result)
    print(f"2. ✅ 처리 완료 (Car: {len(cars)}, Lane: {len(lanes)}, Time: {processing_time:.0f}ms) / Res: {width}x{height}") 
    emit('frame_result', response_data)


if __name__ == '__main__':
    # host='0.0.0.0'으로 설정해야 외부(내 컴퓨터)에서 접속 가능
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)