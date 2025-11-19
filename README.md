# 하이브리드 클라우드 기반 실시간 차선 & 자동차 감지 시스템 (hybrid-cloud-lane-detection)

## 📖 프로젝트 개요
이 프로젝트는 모바일 카메라로 도로 주행 영상을 촬영하고, **AWS(실시간 처리) + GCE(배치 분석)** 하이브리드 클라우드 아키텍처를 통해 실시간으로 차선과 차량을 감지하여 시각화하는 시스템입니다.

---

## 🚨 AI Agent 작업 지침 (필독)
**AI 어시스턴트(Cursor, Kiro, Antigravity)는 작업을 시작하기 전 아래 파일을 반드시 참조하십시오.**

이 프로젝트는 두 가지 상이한 하드웨어 환경(Desktop/Notebook)에서 진행되므로, 상황에 맞는 코드 제안이 필수적입니다.

* **Claude 기반 (Cursor, Kiro, Claude.ai):**
    * 루트 경로의 **`./CLAUDE.md`**를 먼저 읽으십시오.
    * 현재 사용자가 **Desktop(CUDA)**에 있는지 **Surface Pro(CPU)**에 있는지 확인 후 코드를 생성하십시오.
* **Gemini 기반 (Antigravity):**
    * 루트 경로의 **`./GEMINI.md`**를 먼저 읽으십시오.
    * 교수님의 연구 관심사(논문)와 전체 15일 로드맵의 맥락을 유지하며 답변하십시오.

---

## 🛠️ 개발 환경 (Hardware & Tools)

### 🖥️ Home Desktop (Main Dev & Training)
* **CPU:** Intel Core i7-13700K
* **RAM:** 32GB (DDR4/5)
* **GPU:** NVIDIA RTX 4070 Super (CUDA 가속 활성화)
* **역할:** YOLO 모델 Fine-tuning, Docker 컨테이너 다중 실행, 부하 테스트, 백엔드 로직 헤비 테스팅

### 💻 Notebook - Surface Pro 8 (Mobility & Frontend)
* **CPU:** Intel Core i5-1135G7
* **RAM:** 16GB
* **GPU:** Intel Iris Xe (내장 그래픽)
* **역할:** React Native 프론트엔드 개발, API 연동 테스트, 문서 작업, 가벼운 백엔드 코드 수정

### 🤖 AI IDE Stack
* **Antigravity:** Gemini 3.0 / Claude Sonnet 4.5 Thinking (아키텍처 설계, 복잡한 로직 해결)
* **Cursor:** Student Plan (실시간 코딩 보조, 리팩토링)
* **Kiro:** Claude 4.5 기반 (프로젝트 관리, 문서화)

## 🏗️ 시스템 아키텍처
1.  **Frontend:** React Native (Mobile) -> WebSocket -> AWS ALB
2.  **AWS Layer:** ALB -> EC2 (Flask/FastAPI + OpenCV/YOLO) -> Auto Scaling
3.  **Storage:** AWS S3 (이미지 저장) / AWS RDS (메타데이터)
4.  **GCE Layer:** GCE Instance (배치 분석, 합성 데이터 생성)

## 🚀 시작 가이드 (Getting Started)

### Desktop 환경 설정 (CUDA 권장)
```bash
# Desktop에서는 GPU 가속을 사용합니다
pip install -r requirements-desktop.txt
# PyTorch with CUDA 설치 필요

### Notebook 환경 설정 (Surface Pro 8)
```bash
# Notebook에서는 경량화 설정을 사용합니다
pip install -r requirements-surface.txt
# CPU 전용 PyTorch 설치 (용량 절약)