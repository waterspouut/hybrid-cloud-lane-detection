from flask import Flask
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
from core.lane_detector import LaneDetector
from core.object_detector import ObjectDetector
import time

app = Flask(__name__)
# cors_allowed_origins='*': 모든 곳에서의 접속 허용
socketio = SocketIO(app, cors_allowed_origins="*")

# 감지기 인스턴스 생성
lane_detector = LaneDetector()
# YOLO 모델 로드 (CPU 환경이므로 nano 모델 사용)
object_detector = ObjectDetector(model_size='n')


@app.route('/')
def index():
    return "Hybrid Cloud Lane Detection API is Running!"


@socketio.on('connect')
def handle_connect():
    print("Client connected")


@socketio.on('process_frame')
def handle_frame(data):
    """
    클라이언트(앱)가 'process_frame' 이벤트로 이미지를 보내면 호출됩니다.
    """
    start_time = time.time()

    # 1. Base64 이미지 디코딩
    try:
        # [수정 포인트] 딕셔너리에서 'image' 키로 데이터를 꺼냅니다.
        image_data = base64.b64decode(data['image'])
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Image decode error: {e}")
        return

    if frame is None:
        return

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
        "processing_time": processing_time
    }

    # 요청을 보낸 클라이언트에게 결과 반환 (이벤트명: frame_result)
    emit('frame_result', response_data)


if __name__ == '__main__':
    # host='0.0.0.0'으로 설정해야 외부(내 컴퓨터)에서 접속 가능
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)