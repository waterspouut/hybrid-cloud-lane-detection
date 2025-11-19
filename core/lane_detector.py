import cv2
import numpy as np

class LaneDetector:
    def __init__(self):
        pass

    def detect(self, image):
        """
        Detect lanes in the image using Hough Transform.
        Returns the image with lanes drawn.
        """
        if image is None:
            return None

        # 1. Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Gaussian Blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Canny Edge Detection
        edges = cv2.Canny(blur, 50, 150)

        # 4. Region of Interest (ROI)
        height, width = edges.shape
        mask = np.zeros_like(edges)
        
        # Define a triangular polygon for the ROI (bottom half of the screen)
        polygon = np.array([
            [(0, height), (width // 2, height // 2), (width, height)]
        ], np.int32)
        
        cv2.fillPoly(mask, polygon, 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        # 5. Hough Transform
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=150)

        # 6. Draw lines on the original image
        line_image = np.zeros_like(image)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 5)

        # Combine original image with line image
        result = cv2.addWeighted(image, 0.8, line_image, 1, 1)
        return result