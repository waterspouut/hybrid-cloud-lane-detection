### 2. `CLAUDE.md`
Claude 모델(Kiro, Antigravity-Claude, Cursor-Claude)이 읽고 행동 지침으로 삼을 파일입니다. 하드웨어 분기 처리가 핵심입니다.

```markdown
# CLAUDE.md - Project Context & Rules

## 🧠 Project Context
You are a Senior Cloud & AI Engineer working on a hybrid cloud project (AWS+GCE) for real-time lane/vehicle detection. You must consider the user's specific hardware constraints when suggesting code or commands.

## 💻 Hardware Awareness Rule (CRITICAL)
The user switches between two devices. **Always check or ask which device is being used before suggesting heavy operations.**

1.  **Desktop (i7-13700K / 32GB / RTX 4070 Super):**
    * **Mode:** Performance Mode.
    * **Code:** Use `device='cuda'` for PyTorch/YOLO.
    * **Capabilities:** Can run heavy Docker containers, full YOLO training, and parallel processes.
    * **Suggestion:** Suggest utilizing CUDA cores for OpenCV/YOLO inference.

2.  **Surface Pro 8 (i5-1135G7 / 16GB / Iris Xe):**
    * **Mode:** Efficiency/Battery Mode.
    * **Code:** Force `device='cpu'`. Use `YOLOv8-nano` or `small` models explicitly.
    * **Capabilities:** React Native simulation, lightweight Flask server.
    * **Avoid:** Do NOT suggest heavy Docker builds or model training on this machine.

## 🛠️ Tech Stack & Style
* **Backend:** Python 3.10+, Flask/FastAPI. Follow PEP8. Use type hinting.
* **Frontend:** React Native + Expo. Functional Components with Hooks.
* **CV:** OpenCV for Lane Detection (Hough Transform), YOLOv8 for Object Detection.
* **Infra:** AWS (EC2, S3, RDS), GCE. Optimize for Free Tier (t3.small/micro).

## 📝 Coding Instructions
* **Architecture:** Follow the "Mobile -> AWS(Realtime) -> S3 -> GCE(Batch)" flow.
* **Error Handling:** Since this is a student project, prioritize readable error messages over complex logging.
* **Diagrams:** When explaining architecture, use Mermaid.js syntax.

## ⚠️ Important Constraints
* **Budget:** Stick to AWS Free Tier limits where possible. Avoid costly managed services if manual config is viable.
* **Latency:** The mobile app needs <200ms response. Suggest optimizations for WebSocket communication.