from flask import Flask
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
from core.lane_detector import LaneDetector
from core.object_detector import ObjectDetector
import time
import threading  # 추가: 백그라운드 작업을 위한 스레드 모듈
import boto3      # 추가: AWS S3 연동 라이브러리
from datetime import datetime # 추가: 파일명 생성을 위한 시간 모듈

app = Flask(__name__)
# cors_allowed_origins='*': 모든 곳에서의 접속 허용
# max_http_buffer_size: 기본 1MB -> 10MB로 증설 (고해상도 이미지 전송 대비)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10*1024*1024)

# --- [설정 추가] ---
# S3 버킷 이름 (아까 만든 이름으로 꼭 바꾸세요!)
S3_BUCKET_NAME = 'lane-data-2025-oreum' 
SAVE_INTERVAL = 3.0  # 3초에 한 번씩만 저장 (데이터 수집용)
last_save_time = 0   # 마지막으로 저장한 시간 기록용 변수

# 감지기 인스턴스 생성
lane_detector = LaneDetector()
# YOLO 모델 로드 (CPU 환경이므로 nano 모델 사용)
object_detector = ObjectDetector(model_size='n')
# boto3 S3 클라이언트 생성 (서버에 설정된 권한 정보 사용)
s3 = boto3.client('s3')


# --- [함수 추가] ---
def upload_to_s3_background(image, filename):
    """
    백그라운드 스레드에서 S3로 이미지를 업로드하는 함수입니다.
    메인 스레드의 실시간 처리를 방해하지 않기 위해 별도로 동작합니다.
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
        print(f"💾 S3 저장 성공: {filename}")
    except Exception as e:
        print(f"⚠️ S3 업로드 실패: {e}")


@app.route('/')
def index():
    return "Hybrid Cloud Lane Detection API is Running with S3 Storage!"


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

    # --- [데이터 수집 로직 시작] ---
    # 3초마다 한 번씩 원본 이미지를 S3에 저장합니다.
    current_time = time.time()
    if current_time - last_save_time > SAVE_INTERVAL:
        last_save_time = current_time
        # 파일명 생성: YYYYMMDD_HHMMSS_ffffff.jpg (예: 20251120_143001_123456.jpg)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
        # 메인 로직이 멈추지 않게 별도 스레드(thread)로 업로드 작업을 보냅니다.
        # args=(frame.copy(), ...) : 현재 프레임의 복사본을 넘겨야 안전합니다.
        threading.Thread(target=upload_to_s3_background, args=(frame.copy(), filename)).start()
    # --- [데이터 수집 로직 끝] ---


    # 이미지 크기 확인 (클라이언트 스케일링용)
    height, width = frame.shape[:2]

    # 2. 차선 감지 (좌표 리스트 반환)
    lanes = lane_detector.detect(frame)

    # 3. 객체(자동차) 감지 (좌표 리스트 반환)
    cars = object_detector.detect(frame)

    # 4. 처리 시간 계산
    processing_time = (time.time() - start_time) * 1000  # ms 단위

    # 5. 결과 전송 (JSON 형식 - 모바일 앱에서 그리도록)
    response_data = {
        "lanes": lanes,
        "cars": cars,
        "processing_time": processing_time,
        "image_width": width,   # [추가] 서버가 처리한 이미지 너비
        "image_height": height  # [추가] 서버가 처리한 이미지 높이
    }

    # 요청을 보낸 클라이언트에게 결과 반환 (이벤트명: frame_result)
    print(f"2. ✅ 처리 완료 (소요시간: {(time.time() - start_time)*1000:.0f}ms) / Res: {width}x{height}") 
    emit('frame_result', response_data)


if __name__ == '__main__':
    # host='0.0.0.0'으로 설정해야 외부(내 컴퓨터)에서 접속 가능
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)