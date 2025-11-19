import cv2
import numpy as np
import base64

def base64_to_image(base64_string):
    """
    Convert base64 string to OpenCV image.
    """
    # Remove header if present (e.g., "data:image/jpeg;base64,")
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    img_data = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

def image_to_base64(image):
    """
    Convert OpenCV image to base64 string.
    """
    _, buffer = cv2.imencode('.jpg', image)
    base64_string = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_string}"
