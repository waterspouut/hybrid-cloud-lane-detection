from ultralytics import YOLO
import cv2


class ObjectDetector:
    def __init__(self, model_size='n'):
        # 모델 로드: 'yolov8n.pt' (nano 버전 - 가장 빠름)
        self.model = YOLO(f'yolov8{model_size}.pt')

    def detect(self, image):
        """
        이미지를 받아 자동차(car, bus, truck)의 위치를 반환합니다.
        """
        results = self.model(image, verbose=False)  # verbose=False: 로그 끄기

        cars = []
        # 결과 파싱
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]

                # 자동차 계열만 필터링 (car, bus, truck, motorcycle)
                if class_name in ['car', 'bus', 'truck', 'motorcycle']:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])

                    cars.append({
                        "label": class_name,
                        "bbox": [x1, y1, x2, y2],  # 경계 상자 좌표
                        "confidence": conf
                    })
        return cars