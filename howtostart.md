1. 백엔드 서버 열기(AWS)

powershell에서 실행

ssh -i "lane-project-key.pem" ubuntu@15.165.177.0

키 파일 권한 에러가 나면 ~/lane-project-key.pem 확인

2. 가상환경 켜기

AWS 접속 후 

cd ~/lane-project      # 프로젝트 폴더로 이동
source venv/bin/activate
# (터미널 앞에 (venv) 라고 뜨면 성공)

서버 실행
python app.py


3. 프론트엔드 앱 열기

Powershell
cd LaneApp
npx expo start (-c)

4. 파일 업로드 (SCP)

파일 하나 보낼때
scp -i "lane-project-key.pem" app.py ubuntu@15.165.177.0:/home/ubuntu/lane-project/

폴더 통째로 보낼 때
# -r 옵션 추가
scp -i "lane-project-key.pem" -r core/ ubuntu@15.165.177.0:/home/ubuntu/lane-project/

💡 요약 순서 (개발 루틴)
백엔드 켜기: SSH 접속 -> source venv/bin/activate -> python app.py

프론트엔드 켜기: 내 컴퓨터에서 npx expo start -> 폰으로 QR 스캔

테스트: 폰으로 모니터(도로 영상) 비추기 -> FPS 올라가는지 확인

수정 필요 시:

백엔드 수정함 -> scp로 업로드 -> AWS에서 Ctrl+C 후 다시 python app.py

프론트 수정함 -> 저장하면 폰에서 자동 반영됨