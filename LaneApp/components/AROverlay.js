import React from 'react';
import { View, StyleSheet, Text } from 'react-native';
import Svg, { Line, Rect, Text as SvgText } from 'react-native-svg';

const AROverlay = ({ 
  lanes = [], 
  cars = [], 
  width, 
  height, 
  fps = 0, 
  processingTime = 0,
  serverWidth = 640, 
  serverHeight = 480 
}) => {
  
  if (!width || !height || !serverWidth || !serverHeight) return null;

  const scaleX = width / serverWidth;
  const scaleY = height / serverHeight;

  // --- 거리 계산 로직 (Geometric Estimation) ---
  // 가정: 평균 자동차 폭 = 1.8m
  // 가정: 스마트폰 카메라 화각(FOV)에 따른 초점거리 상수 (보정 필요할 수 있음)
  const REAL_CAR_WIDTH = 1.8; 
  const FOCAL_LENGTH_FACTOR = serverWidth * 1.2; // 대략적인 초점거리 상수

  const getDistance = (bboxWidth) => {
    if (bboxWidth <= 0) return 0;
    // 거리 = (실제크기 * 초점거리) / 픽셀크기
    const distance = (REAL_CAR_WIDTH * FOCAL_LENGTH_FACTOR) / bboxWidth;
    return distance;
  };

  // --- 차선 폭 계산 로직 ---
  // 바닥(y=height)에서의 좌우 차선 간격 픽셀을 미터로 변환
  // 가정: 바닥면 전체 너비가 약 5~6m 정도의 시야를 가짐
  const ROAD_VIEW_WIDTH_M = 5.5; 

  let laneWidthM = 0;
  const leftLane = lanes.find(l => l.id === 'left');
  const rightLane = lanes.find(l => l.id === 'right');

  if (leftLane && rightLane) {
    const leftX = leftLane.x1;  // 바닥 x좌표
    const rightX = rightLane.x1; // 바닥 x좌표
    const pixelDist = Math.abs(rightX - leftX);
    laneWidthM = (pixelDist / serverWidth) * ROAD_VIEW_WIDTH_M;
  }

  return (
    <View style={styles.container} pointerEvents="none">
      <Svg height={height} width={width} style={styles.svg}>
        
        {/* 1. 차선 그리기 */}
        {lanes.map((lane, index) => (
          <Line
            key={`lane-${index}`}
            x1={lane.x1 * scaleX}
            y1={lane.y1 * scaleY}
            x2={lane.x2 * scaleX}
            y2={lane.y2 * scaleY}
            stroke={lane.id === 'left' ? "#00FF00" : "#FF0000"} 
            strokeWidth="6"
            strokeOpacity="0.6"
          />
        ))}

        {/* 2. 자동차 박스 및 거리 표시 */}
        {cars.map((car, index) => {
          const [x1, y1, x2, y2] = car.bbox;
          const boxWidth = (x2 - x1);
          const distance = getDistance(boxWidth);
          
          // 위험 거리 경고 (15m 미만)
          const isDanger = distance < 15;
          const color = isDanger ? "#FF0000" : "#00AAFF";

          return (
            <React.Fragment key={`car-${index}`}>
              <Rect
                x={x1 * scaleX}
                y={y1 * scaleY}
                width={boxWidth * scaleX}
                height={(y2 - y1) * scaleY}
                stroke={color}
                strokeWidth="3"
                fill={isDanger ? "rgba(255, 0, 0, 0.2)" : "rgba(0, 170, 255, 0.1)"}
              />
              <SvgText
                x={x1 * scaleX}
                y={(y1 * scaleY) - 25}
                fill={color}
                fontSize="20"
                fontWeight="bold"
                stroke="black"
                strokeWidth="1"
              >
                {`${distance.toFixed(1)}m`}
              </SvgText>
              <SvgText
                x={x1 * scaleX}
                y={(y1 * scaleY) - 5}
                fill="white"
                fontSize="14"
                fontWeight="bold"
              >
                {`${car.label} ${(car.confidence * 100).toFixed(0)}%`}
              </SvgText>
            </React.Fragment>
          );
        })}
      </Svg>

      {/* 3. HUD 정보 */}
      <View style={styles.hud}>
        <Text style={styles.hudTitle}>🚀 ADAS SYSTEM</Text>
        <View style={styles.hudRow}>
          <Text style={styles.hudLabel}>FPS:</Text>
          <Text style={styles.hudValue}>{fps}</Text>
        </View>
        <View style={styles.hudRow}>
          <Text style={styles.hudLabel}>Lane Width:</Text>
          <Text style={styles.hudValue}>
            {laneWidthM > 0 ? `${laneWidthM.toFixed(1)}m` : "Detecting..."}
          </Text>
        </View>
        {cars.length > 0 && (
          <View style={styles.hudRow}>
            <Text style={styles.hudLabel}>Nearest:</Text>
            <Text style={[styles.hudValue, { color: '#FF5555' }]}>
              {getDistance(cars[0].bbox[2] - cars[0].bbox[0]).toFixed(1)}m
            </Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 10,
  },
  svg: {
    flex: 1,
  },
  hud: {
    position: 'absolute',
    top: 50,
    left: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 15,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  hudTitle: {
    color: '#00FF00',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  hudRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
    minWidth: 140,
  },
  hudLabel: {
    color: '#CCCCCC',
    fontSize: 16,
    marginRight: 10,
  },
  hudValue: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default AROverlay;