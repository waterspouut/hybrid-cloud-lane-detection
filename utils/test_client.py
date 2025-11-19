import socketio
import cv2
import base64
import numpy as np
import time

# 1. 서버 주소 설정 (방금 성공한 그 주소!)
# 주의: http:// 입니다.
SERVER_URL = 'http://15.165.177.0:5000'

# 2. 소켓 클라이언트 생성
sio = socketio.Client()


@sio.event
def connect():
    print("✅ 서버에 연결되었습니다!")

    # 3. 테스트할 이미지 읽기 (프로젝트 폴더에 아무 이미지나 'test.jpg'로 넣어두세요)
    # 이미지가 없다면 검은 화면을 만들어서 보냅니다.
    try:
        img = cv2.imread('test.jpg')
        if img is None:
            print("⚠️ test.jpg가 없어서 검은 화면을 생성합니다.")
            img = np.zeros((480, 640, 3), dtype=np.uint8)
    except:
        img = np.zeros((480, 640, 3), dtype=np.uint8)

    # 4. 이미지를 JPG -> Base64 문자열로 변환
    _, buffer = cv2.imencode('.jpg', img)
    img_str = base64.b64encode(buffer).decode('utf-8')

    # 5. 서버로 전송 ('process_frame' 이벤트)
    print("📤 이미지를 서버로 전송합니다...")
    sio.emit('process_frame', {'image': img_str})


@sio.on('frame_result')
def on_result(data):
    print("\n📩 서버로부터 응답이 왔습니다!")
    print(f"⏱️ 처리 시간: {data['processing_time']:.2f}ms")
    print(f"🛣️ 감지된 차선 수: {len(data['lanes'])}")
    print(f"🚗 감지된 차량 수: {len(data['cars'])}")

    # 연결 종료
    sio.disconnect()


@sio.event
def disconnect():
    print("❌ 연결이 종료되었습니다.")


if __name__ == '__main__':
    try:
        sio.connect(SERVER_URL)
        sio.wait()
    except Exception as e:
        print(f"연결 실패: {e}")