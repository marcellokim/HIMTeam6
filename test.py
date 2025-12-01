import pandas as pd
import os
import json
import glob
import numpy as np

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
SURVEY_PATH = './사후 설문 정리.csv'
JSON_DIR = './data'
RESULT_DIR = './results'

if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# ==========================================
# 2. JSON에서 참가자별 실험 순서 추출
# ==========================================
print("🔄 실험 순서 데이터 추출 중...")

participant_orders = {}

json_files = glob.glob(os.path.join(JSON_DIR, '*.json'))
for jf in json_files:
    try:
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
            name = data['participant']['name'].strip()

            # experiments 리스트에 저장된 순서가 실제 수행 순서입니다.
            # 예: ['fixed', 'bottom-right', 'adaptive']
            orders = []
            for exp in data['experiments']:
                orders.append(exp['condition'])

            participant_orders[name] = orders
    except Exception as e:
        print(f"⚠️ JSON 로드 에러 ({jf}): {e}")

print(f"✅ 총 {len(participant_orders)}명의 순서 정보 확보")

# ==========================================
# 3. 설문 데이터 로드 및 정밀 매핑
# ==========================================
try:
    df_raw = pd.read_csv(SURVEY_PATH)
except Exception as e:
    print(f"❌ 설문 CSV 파일을 찾을 수 없습니다: {e}")
    exit()

mapped_data = []

# 설문 문항 키워드 (CSV 컬럼명에 포함된 단어)
metric_keyword_map = {
    '신체적 노력': 'Physical_Effort',
    '접근성': 'Accessibility',
    '그립 안정성': 'Grip_Instability' # 점수가 높을수록 불안정함
}

# 질문 번호(4,5,6)와 순서 인덱스(0,1,2) 매핑
ordinal_map_q = {4: 0, 5: 1, 6: 2}

print("🔄 설문 데이터 매핑 및 검증 중...")

for idx, row in df_raw.iterrows():
    name = str(row.get('1. 성함', '')).strip()

    # JSON 로그가 없는 참가자는 제외 (순서를 모르므로)
    if not name or name not in participant_orders:
        continue

    order = participant_orders[name] # 예: ['fixed', 'adaptive', 'bottom-right']

    # 1. 기본 정보 저장
    p_data = {
        'Participant': name,
        'Order_1st': order[0],
        'Order_2nd': order[1],
        'Order_3rd': order[2]
    }

    # 2. 점수 매핑
    for col in df_raw.columns:
        # 컬럼명이 "4-1", "5-2" 등으로 시작하는지 확인
        header_part = str(col).split('.')[0] # "4-1" 추출
        if '-' in header_part:
            try:
                q_num = int(header_part.split('-')[0]) # 4, 5, 6
                if q_num in ordinal_map_q:
                    order_idx = ordinal_map_q[q_num] # 0, 1, 2
                    condition = order[order_idx]     # 해당 순서의 조건명 (fixed 등)

                    # 지표 확인 및 매핑
                    for keyword, metric_name in metric_keyword_map.items():
                        if keyword in col:
                            # 컬럼명 예: Fixed_Physical_Effort
                            p_data[f'{condition}_{metric_name}'] = row[col]
                            break
            except:
                continue

    # 3. 선호도(종합 순위) 매핑
    def clean_pref(val):
        val_str = str(val)
        if '첫 번째' in val_str: return order[0]
        if '두 번째' in val_str: return order[1]
        if '세 번째' in val_str: return order[2]
        return val_str # 매칭 안되면 원본 반환

    # CSV 컬럼명에 따라 수정 필요할 수 있음
    for col in df_raw.columns:
        if '[1순위]' in col: p_data['Best_Choice'] = clean_pref(row[col])
        if '[2순위]' in col: p_data['Second_Choice'] = clean_pref(row[col])
        if '[3순위]' in col: p_data['Third_Choice'] = clean_pref(row[col])

    mapped_data.append(p_data)

# 데이터프레임 생성
df_mapped = pd.DataFrame(mapped_data)

# ==========================================
# 4. 검증용 CSV 저장 및 요약 출력
# ==========================================
# 컬럼 순서 보기 좋게 정렬 (Participant, Best_Choice, Fixed_..., Adaptive_..., Bottom_...)
cols = ['Participant', 'Best_Choice']
for cond in ['fixed', 'adaptive', 'bottom-right']:
    for met in ['Physical_Effort', 'Accessibility', 'Grip_Instability']:
        col_name = f'{cond}_{met}'
        if col_name in df_mapped.columns:
            cols.append(col_name)

# 존재하는 컬럼만 선택하여 재정렬
final_cols = [c for c in cols if c in df_mapped.columns]
df_final = df_mapped[final_cols]

# CSV 저장
save_path = os.path.join(RESULT_DIR, 'mapped_survey_data_check.csv')
df_final.to_csv(save_path, index=False, encoding='utf-8-sig')

print(f"\n💾 검증 데이터 저장 완료: {save_path}")
print("   -> 이 파일을 열어서 'Adaptive_Grip_Instability' 등의 점수가 맞는지 확인하세요.")

# ==========================================
# 5. [즉시 확인용] 조건별 평균 점수 출력
# ==========================================
print("\n📊 [중간 점검] 조건별 평균 점수 (4.7점의 정체 확인)")
print("-" * 50)
for cond in ['fixed', 'adaptive', 'bottom-right']:
    print(f"Condition: {cond}")
    for met in ['Physical_Effort', 'Accessibility', 'Grip_Instability']:
        col = f'{cond}_{met}'
        if col in df_final.columns:
            avg = pd.to_numeric(df_final[col], errors='coerce').mean()
            print(f"  - {met}: {avg:.2f}")
print("-" * 50)