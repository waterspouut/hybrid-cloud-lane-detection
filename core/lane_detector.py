import cv2
import numpy as np

class LaneDetector:
    def __init__(self):
        # 이전 프레임의 차선 정보를 저장해두었다가, 
        # 현재 프레임에서 차선을 못 찾으면 대신 사용 (깜빡임 방지)
        self.prev_left = None
        self.prev_right = None

    def make_coordinates(self, image, line_parameters):
        """
        기울기(slope)와 절편(intercept)을 받아서
        이미지 상의 실제 좌표 (x1, y1, x2, y2)를 계산합니다.
        """
        if line_parameters is None:
            return None
            
        slope, intercept = line_parameters
        y1 = image.shape[0]  # 화면 바닥
        y2 = int(y1 * 0.6)   # 화면의 60% 지점 (소실점 부근)
        
        # y = mx + b  ->  x = (y - b) / m
        if slope == 0: 
            slope = 0.001 # 0 나누기 방지
            
        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)
        
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    def average_slope_intercept(self, image, lines):
        """
        여러 개의 선분들을 받아서 왼쪽 차선과 오른쪽 차선으로 분류하고,
        각각의 평균을 구해서 '하나의 대표 차선'으로 만듭니다.
        """
        left_fit = []
        right_fit = []
        
        if lines is None:
            return None, None

        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 수직선 예외처리
            if x1 == x2:
                continue
                
            # 1. 기울기 및 절편 계산 (y = mx + b)
            parameters = np.polyfit((x1, x2), (y1, y2), 1)
            slope = parameters[0]
            intercept = parameters[1]
            
            # 2. 기울기 필터링 (너무 완만하거나 수직인 선 제거)
            # 왼쪽 차선: 기울기가 음수 (보통 -2.0 ~ -0.5)
            # 오른쪽 차선: 기울기가 양수 (보통 0.5 ~ 2.0)
            if slope < -0.5 and slope > -2.0:
                left_fit.append((slope, intercept))
            elif slope > 0.5 and slope < 2.0:
                right_fit.append((slope, intercept))
                
        # 3. 평균 계산
        left_line = None
        right_line = None
        
        if len(left_fit) > 0:
            left_avg = np.average(left_fit, axis=0)
            left_line = self.make_coordinates(image, left_avg)
            self.prev_left = left_line # 저장
        else:
            left_line = self.prev_left # 못 찾으면 이전 값 사용

        if len(right_fit) > 0:
            right_avg = np.average(right_fit, axis=0)
            right_line = self.make_coordinates(image, right_avg)
            self.prev_right = right_line # 저장
        else:
            right_line = self.prev_right # 못 찾으면 이전 값 사용
            
        return left_line, right_line

    def detect(self, image):
        if image is None:
            return []

        # 1. 그레이스케일
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. 블러 (노이즈 제거 강화)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. 엣지 검출
        edges = cv2.Canny(blur, 50, 150)
        
        # 4. ROI 설정 (대시보드 제외)
        height, width = edges.shape
        mask = np.zeros_like(edges)
        
        polygon = np.array([
            [
                (0, height),                        # 좌측 하단
                (int(width * 0.1), int(height * 0.6)),   # 좌측 상단
                (int(width * 0.9), int(height * 0.6)),   # 우측 상단
                (width, height)                     # 우측 하단
            ]
        ], np.int32)
        
        # 대시보드(화면 하단 10%) 가리기
        # 차 보닛이 차선으로 인식되는 것을 방지
        dashboard_mask = np.ones_like(edges) * 255
        cv2.rectangle(dashboard_mask, (0, int(height * 0.9)), (width, height), 0, -1)
        
        cv2.fillPoly(mask, polygon, 255)
        
        # ROI + 대시보드 마스킹 적용
        masked_edges = cv2.bitwise_and(edges, mask)
        masked_edges = cv2.bitwise_and(masked_edges, dashboard_mask)

        # 5. 직선 검출
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=100)
        
        # 6. 차선 평균화 (Averaging)
        left_lane, right_lane = self.average_slope_intercept(image, lines)
        
        # 결과 리스트 생성
        lanes = []
        if left_lane:
            left_lane["id"] = "left" # [추가] ID 부여
            lanes.append(left_lane)
        if right_lane:
            right_lane["id"] = "right" # [추가] ID 부여
            lanes.append(right_lane)
            
        return lanes