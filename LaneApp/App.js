import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, Dimensions } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { StatusBar } from 'expo-status-bar';
import * as ImageManipulator from 'expo-image-manipulator';
import { socket } from './services/socket';
import AROverlay from './components/AROverlay';

const SCREEN_WIDTH = Dimensions.get('window').width;
const SCREEN_HEIGHT = Dimensions.get('window').height;

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [lanes, setLanes] = useState([]);
  const [cars, setCars] = useState([]);
  const [fps, setFps] = useState(0);
  const [processingTime, setProcessingTime] = useState(0);
  const [serverRes, setServerRes] = useState({ width: 640, height: 480 }); // 서버 처리 해상도
  
  const cameraRef = useRef(null);
  const lastSentTime = useRef(0);
  const isProcessing = useRef(false);

  useEffect(() => {
    // 1. 소켓 연결 이벤트 설정
    socket.on('connect', () => {
      console.log('✅ 서버에 연결되었습니다 (Socket.io)');
    });

    socket.on('frame_result', (data) => {
      // 서버에서 분석 결과가 오면 상태 업데이트
      setLanes(data.lanes || []);
      setCars(data.cars || []);
      setProcessingTime(data.processing_time || 0);
      
      // 서버가 처리한 실제 이미지 크기 업데이트 (좌표 스케일링용)
      if (data.image_width && data.image_height) {
        setServerRes({ width: data.image_width, height: data.image_height });
      }
      
      // FPS 계산
      const now = Date.now();
      const delta = now - lastSentTime.current;
      if (delta > 0) {
        setFps(Math.round(1000 / delta));
      }
      
      isProcessing.current = false; // 다음 프레임 처리 준비 완료
    });

    socket.on('disconnect', () => {
      console.log('❌ 서버와 연결이 끊어졌습니다');
    });

    return () => {
      socket.off('connect');
      socket.off('frame_result');
      socket.off('disconnect');
    };
  }, []);

  // 2. 프레임 캡처 및 전송 루프
  useEffect(() => {
    const intervalId = setInterval(async () => {
      if (
        cameraRef.current && 
        !isProcessing.current && 
        (Date.now() - lastSentTime.current > 150) 
      ) {
        try {
          isProcessing.current = true; 
          lastSentTime.current = Date.now();

          // 1. 사진 캡처
          const photo = await cameraRef.current.takePictureAsync({
            quality: 0.5,
            base64: false, 
            skipProcessing: true,
            imageType: 'jpg',
          });

          // 2. 이미지 리사이징 (640px 너비)
          // 세로 모드일 경우 높이가 640보다 커질 수 있음 (예: 640x853)
          // 서버는 이 비율 그대로 받아서 처리하고, 그 크기를 다시 알려줌
          const manipulated = await ImageManipulator.manipulateAsync(
            photo.uri,
            [{ resize: { width: 640 } }], 
            { compress: 0.5, format: ImageManipulator.SaveFormat.JPEG, base64: true }
          );

          // 3. 서버로 전송
          if (manipulated.base64) {
            socket.emit('process_frame', { image: manipulated.base64 });
          } else {
            isProcessing.current = false;
          }
        } catch (error) {
          console.error("📷 프레임 캡처/전송 에러:", error);
          isProcessing.current = false; 
        }
      }
    }, 50); 

    return () => clearInterval(intervalId);
  }, [permission]);

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>카메라 권한이 필요합니다</Text>
        <Text style={styles.permissionButton} onPress={requestPermission}>권한 허용하기</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      
      {/* CameraView: 배경 카메라 */}
      <CameraView
        style={StyleSheet.absoluteFill}
        facing="back"
        ref={cameraRef}
        animateShutter={false}
      />
      
      {/* AROverlay: 카메라 위에 겹쳐지는 오버레이 */}
      <AROverlay 
        lanes={lanes} 
        cars={cars} 
        width={SCREEN_WIDTH} 
        height={SCREEN_HEIGHT}
        fps={fps}
        processingTime={processingTime}
        serverWidth={serverRes.width}   // 동적 전달
        serverHeight={serverRes.height} // 동적 전달
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'black',
    justifyContent: 'center',
    alignItems: 'center',
  },
  permissionText: {
    textAlign: 'center',
    marginBottom: 20,
    color: 'white',
    fontSize: 18,
  },
  permissionButton: {
    color: '#007AFF',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
});