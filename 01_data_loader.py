import json
import pandas as pd
import numpy as np
import os
import math
import glob

# ==========================================
# 1. 설정 및 준비
# ==========================================
DATA_DIR = './data'      # JSON 파일이 있는 폴더
RESULT_DIR = './results' # 결과를 저장할 폴더

if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# ==========================================
# 2. 데이터 로딩 함수
# ==========================================
def load_and_process_data(data_dir):
    json_pattern = os.path.join(data_dir, '*.json')
    file_list = glob.glob(json_pattern)

    if not file_list:
        print(f"❌ 오류: '{data_dir}' 폴더에 .json 파일이 없습니다. 파일 위치를 확인하세요.")
        return None, None

    print(f"📂 총 {len(file_list)}개의 데이터 파일을 찾았습니다.")

    all_trials = []
    user_metadata = []

    for file_path in file_list:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            participant_id = data['participant']['name']

            # 1) 개인화 정보 (Reachable Radius) 추출
            radius = np.nan
            if data.get('circleData'):
                radius = data['circleData']['radius']

            user_metadata.append({
                'Participant': participant_id,
                'Radius': radius
            })

            # 2) 실험 데이터 추출
            for exp in data['experiments']:
                condition = exp['condition']

                for trial in exp['trials']:
                    # Search Time = 전체 시간 - 타이핑 시간
                    completion_time = trial['completionTime']
                    typing_time = trial['typingTime']
                    search_time = completion_time - typing_time

                    # Offset (정확도) 계산
                    # buttonPosition은 항상 있지만, buttonTouchPosition은 없을 수도 있음(오류 등)
                    btn_pos = trial['buttonPosition']
                    touch_pos = trial.get('buttonTouchPosition')

                    offset = np.nan
                    if touch_pos:
                        # 유클리드 거리 공식: sqrt((x1-x2)^2 + (y1-y2)^2)
                        dx = btn_pos['x'] - touch_pos['x']
                        dy = btn_pos['y'] - touch_pos['y']
                        offset = math.sqrt(dx**2 + dy**2)

                    # 타겟의 Y 위치 (상단/중단/하단 분석용)
                    target_y = btn_pos['y']

                    all_trials.append({
                        'Participant': participant_id,
                        'Condition': condition,
                        'Trial_Order': trial['trial'],
                        'SearchTime': search_time,
                        'TypingTime': typing_time,
                        'CompletionTime': completion_time,
                        'Offset': offset,
                        'Error': 1 if trial['error'] else 0,
                        'Target_Y': target_y,
                        'Reachable_Radius': radius
                    })

        except Exception as e:
            print(f"⚠️ 경고: {file_path} 처리 중 오류 발생 - {e}")

    df_trials = pd.DataFrame(all_trials)
    df_users = pd.DataFrame(user_metadata)

    return df_trials, df_users

# ==========================================
# 3. 실행 및 검증 리포트
# ==========================================
print("🔄 데이터 로딩 중...")
df, df_users = load_and_process_data(DATA_DIR)

if df is not None:
    print("\n" + "="*40)
    print("✅ 데이터 로딩 성공 보고서")
    print("="*40)

    # 1. 기본 수량 체크
    print(f"1. 총 참가자 수: {df['Participant'].nunique()}명")
    print(f"2. 총 시행(Trial) 수: {len(df)}건")

    # 2. 조건별 데이터 균형 체크 (각 조건별로 시행 횟수가 비슷한지)
    print("\n3. 조건별 데이터 수 (Conditions):")
    print(df['Condition'].value_counts())

    # 3. 결측치 체크 (Offset이 계산 안 된 경우가 있는지)
    missing_offset = df['Offset'].isnull().sum()
    print(f"\n4. 터치 좌표 누락(Missing Offset): {missing_offset}건")

    # 4. 이상치 사전 점검 (Search Time이 음수거나 너무 짧은 경우)
    invalid_time = df[df['SearchTime'] < 100] # 0.1초 미만은 기계적 오류 가능성
    print(f"5. 비정상 SearchTime (<100ms): {len(invalid_time)}건")

    # 5. 데이터 샘플 (첫 5줄)
    print("\n6. 데이터 미리보기 (상위 5개):")
    print(df[['Participant', 'Condition', 'SearchTime', 'Offset', 'Error']].head())

    # CSV로 중간 저장 (확인용)
    save_path = os.path.join(RESULT_DIR, 'processed_data.csv')
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 전처리된 데이터가 '{save_path}'에 저장되었습니다.")