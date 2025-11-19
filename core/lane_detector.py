import cv2
import numpy as np


class LaneDetector:
    def __init__(self):
        pass

    def detect(self, image):
        """
        이미지를 받아 차선을 감지하고, 감지된 차선 좌표를 반환합니다.
        (모바일 앱 전송용 JSON 포맷 최적화)
        """
        if image is None:
            return []

        # 1. 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. 노이즈 제거 (Gaussian Blur)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. 엣지 검출 (Canny Edge Detection)
        edges = cv2.Canny(blur, 50, 150)

        # 4. 관심 영역(ROI) 설정 - 도로 하단만 보기
        height, width = edges.shape
        mask = np.zeros_like(edges)

        # 삼각형 모양으로 관심 영역 설정
        polygon = np.array([
            [(0, height), (width // 2, height // 2), (width, height)]
        ], np.int32)

        cv2.fillPoly(mask, polygon, 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        # 5. 직선 검출 (Hough Transform)
        # minLineLength: 이 길이보다 짧은 선은 무시
        # maxLineGap: 끊어진 선을 연결하는 허용 간격
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=150)

        lanes = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # 중요: numpy int를 Python int로 변환해야 JSON 전송 시 에러가 안 남
                lanes.append({
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                })

        # 이미지가 아니라 '좌표 리스트'를 반환합니다!
        return lanes