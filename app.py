from flask import Flask
from flask_socketio import SocketIO, emit
import eventlet
import cv2
import numpy as np
import base64
from core.lane_detector import LaneDetector
from core.object_detector import ObjectDetector
from utils.helpers import base64_to_image, image_to_base64

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Detectors
lane_detector = LaneDetector()
object_detector = ObjectDetector()

@app.route('/')
def index():
    return "Hybrid Cloud Lane Detection API is Running!"

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('process_frame')
def handle_frame(data):
    """
    Receive image frame from client, process it, and send back the result.
    Expects data to be a base64 encoded string.
    """
    try:
        # 1. Decode image
        image = base64_to_image(data)
        
        if image is None:
            emit('error', {'message': 'Failed to decode image'})
            return

        # 2. Process Image (Lane Detection + Object Detection)
        # First, detect lanes
        lane_image = lane_detector.detect(image)
        
        # Then, detect objects on top of the lane image
        # (Or you can run them in parallel and combine, but sequential is easier for now)
        final_image = object_detector.detect(lane_image)

        # 3. Encode result
        result_base64 = image_to_base64(final_image)

        # 4. Send back to client
        emit('frame_processed', result_base64)

    except Exception as e:
        print(f"Error processing frame: {e}")
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    # Use eventlet for better WebSocket performance
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)