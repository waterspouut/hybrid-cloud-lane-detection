"""
Auto Scaling Load Test Script
RTX 4070 Super 환경에서 AWS Auto Scaling Group 테스트용
다중 클라이언트 동시 연결로 부하 생성
"""
import socketio
import cv2
import base64
import time
import threading
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np

# 전역 통계
stats = {
    'total_requests': 0,
    'successful': 0,
    'failed': 0,
    'start_time': None,
    'errors': []
}
stats_lock = threading.Lock()

def load_test_client(client_id, server_url, image_path, duration, interval):
    """
    개별 클라이언트 스레드
    Args:
        client_id: 클라이언트 ID
        server_url: 서버 URL (예: http://ALB-DNS:5000)
        image_path: 테스트 이미지 경로
        duration: 테스트 지속 시간 (초)
        interval: 요청 간격 (초)
    """
    # 이미지 로드 (한 번만)
    img = cv2.imread(image_path)
    if img is None:
        print(f"[Client-{client_id}] ❌ Failed to load image: {image_path}")
        return
    
    # YOLO 처리를 위해 크기 조정 (640x640 권장)
    img = cv2.resize(img, (640, 640))
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    end_time = time.time() + duration
    request_count = 0
    
    print(f"[Client-{client_id}] 🚀 Started (Duration: {duration}s, Interval: {interval}s)")
    
    while time.time() < end_time:
        try:
            # 새 SocketIO 클라이언트 생성
            sio = socketio.Client(reconnection=False)
            
            received = threading.Event()
            error_occurred = threading.Event()
            
            @sio.on('detection_result')
            def on_result(data):
                received.set()
            
            @sio.on('error')
            def on_error(data):
                error_occurred.set()
                received.set()
            
            # 연결 및 전송
            sio.connect(server_url, wait_timeout=10)
            
            with stats_lock:
                stats['total_requests'] += 1
            
            # 프레임 전송
            sio.emit('process_frame', img_base64)
            request_count += 1
            
            # 응답 대기 (최대 5초)
            received.wait(timeout=5)
            
            if error_occurred.is_set():
                with stats_lock:
                    stats['failed'] += 1
                print(f"[Client-{client_id}] ⚠️ Request #{request_count} failed")
            else:
                with stats_lock:
                    stats['successful'] += 1
                print(f"[Client-{client_id}] ✅ Request #{request_count} successful")
            
            sio.disconnect()
            
        except Exception as e:
            with stats_lock:
                stats['failed'] += 1
                stats['errors'].append(str(e))
            print(f"[Client-{client_id}] ❌ Error: {e}")
        
        time.sleep(interval)
    
    print(f"[Client-{client_id}] 🏁 Finished ({request_count} requests)")

def print_stats():
    """통계 출력 (1초마다)"""
    while True:
        time.sleep(1)
        with stats_lock:
            elapsed = time.time() - stats['start_time']
            rps = stats['total_requests'] / elapsed if elapsed > 0 else 0
            success_rate = (stats['successful'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
            
            print(f"\n{'='*60}")
            print(f"📊 Load Test Statistics (Elapsed: {elapsed:.1f}s)")
            print(f"{'='*60}")
            print(f"Total Requests: {stats['total_requests']}")
            print(f"Successful: {stats['successful']} ({success_rate:.1f}%)")
            print(f"Failed: {stats['failed']}")
            print(f"Requests/sec: {rps:.2f}")
            print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description='AWS Auto Scaling Load Test')
    parser.add_argument('--server', type=str, default='http://localhost:5000',
                        help='Server URL (예: http://ALB-DNS-HERE.ap-northeast-2.elb.amazonaws.com)')
    parser.add_argument('--clients', type=int, default=10,
                        help='동시 클라이언트 수 (기본: 10)')
    parser.add_argument('--duration', type=int, default=300,
                        help='테스트 지속 시간(초) (기본: 300 = 5분)')
    parser.add_argument('--interval', type=float, default=0.5,
                        help='클라이언트당 요청 간격(초) (기본: 0.5)')
    parser.add_argument('--image', type=str, default='test_road.jpg',
                        help='테스트 이미지 경로')
    
    args = parser.parse_args()
    
    # 이미지 존재 확인
    if not Path(args.image).exists():
        print(f"❌ Image not found: {args.image}")
        return
    
    print(f"""
{'='*60}
🔥 AWS Auto Scaling Load Test
{'='*60}
Server URL: {args.server}
Concurrent Clients: {args.clients}
Duration: {args.duration}s
Request Interval: {args.interval}s
Test Image: {args.image}
{'='*60}
예상 부하: {args.clients / args.interval:.1f} requests/sec
{'='*60}
    """)
    
    # 통계 초기화
    stats['start_time'] = time.time()
    
    # 통계 출력 스레드 시작
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()
    
    # 클라이언트 스레드 생성 및 시작
    threads = []
    for i in range(args.clients):
        t = threading.Thread(
            target=load_test_client,
            args=(i+1, args.server, args.image, args.duration, args.interval)
        )
        t.start()
        threads.append(t)
        time.sleep(0.1)  # 동시 연결 방지 (점진적 증가)
    
    print(f"\n🚀 {args.clients} clients started!\n")
    
    # 모든 스레드 완료 대기
    for t in threads:
        t.join()
    
    # 최종 통계
    print(f"\n{'='*60}")
    print(f"🏁 Load Test Completed!")
    print(f"{'='*60}")
    elapsed = time.time() - stats['start_time']
    print(f"Total Time: {elapsed:.1f}s")
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['successful'] / stats['total_requests'] * 100:.2f}%")
    print(f"Average RPS: {stats['total_requests'] / elapsed:.2f}")
    
    if stats['errors']:
        print(f"\n⚠️ Unique Errors ({len(set(stats['errors']))}):")
        for error in set(stats['errors'])[:5]:  # 처음 5개만 출력
            print(f"  - {error}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
