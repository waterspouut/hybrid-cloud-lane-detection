from ultralytics import YOLO
import cv2
import torch

class ObjectDetector:
    def __init__(self, model_path='yolov8n.pt'):
        # Dynamic device selection based on hardware availability
        # Desktop (RTX 4070S) -> cuda, Surface -> cpu
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Initializing ObjectDetector on device: {self.device}")
        
        self.model = YOLO(model_path)

    def detect(self, image):
        """
        Detect objects (cars) in the image using YOLOv8.
        Returns the image with bounding boxes drawn.
        """
        if image is None:
            return None

        # Perform detection
        results = self.model(image, device=self.device)

        # Plot results on the image
        # results[0].plot() returns the image with boxes drawn
        res_plotted = results[0].plot()
        
        return res_plotted