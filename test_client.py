"""
WebSocket Test Client for Lane Detection API
"""
import socketio
import cv2
import base64
import sys
from pathlib import Path

# Create SocketIO client
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server!")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.on('frame_processed')
def on_frame_processed(data):
    """Handle processed frame from server"""
    print("✅ Received processed frame from server")

    # Decode the base64 image
    # Remove header if present (e.g., "data:image/jpeg;base64,")
    if "," in data:
        data = data.split(",")[1]

    img_bytes = base64.b64decode(data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Save result
    cv2.imwrite('result.jpg', img)
    print("✅ Saved processed image as 'result.jpg'")

    # Disconnect after receiving result
    sio.disconnect()

@sio.on('error')
def on_error(data):
    """Handle error from server"""
    print(f"❌ Error: {data.get('message', 'Unknown error')}")
    sio.disconnect()

def test_api(image_path):
    """Test the API with an image"""
    # Read image
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return

    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read image: {image_path}")
        return

    print(f"✅ Loaded image: {image_path} ({img.shape})")

    # Encode image to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    # Connect to server
    print("🔌 Connecting to server...")
    try:
        sio.connect('http://localhost:5000')

        # Send frame for processing
        print("📤 Sending frame to server...")
        sio.emit('process_frame', img_base64)

        # Wait for response
        sio.wait()

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == '__main__':
    import numpy as np

    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path>")
        print("Example: python test_client.py test_road.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    test_api(image_path)
