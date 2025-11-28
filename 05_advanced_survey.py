import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import glob
import platform

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
SURVEY_PATH = './사후 설문 정리.csv'
JSON_DIR = './data'
RESULT_DIR = './results'

if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# 폰트 설정
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

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

            orders = []
            for exp in data['experiments']:
                orders.append(exp['condition'])

            participant_orders[name] = orders
    except Exception as e:
        print(f"⚠️ JSON 로드 에러 ({jf}): {e}")

print(f"✅ 총 {len(participant_orders)}명의 순서 정보 확보")

# ==========================================
# 3. 설문 데이터 로드 및 매핑
# ==========================================
try:
    df_raw = pd.read_csv(SURVEY_PATH)
    print(f"✅ 설문 파일 로드 성공: {len(df_raw)}명 응답")
except Exception as e:
    print(f"❌ 설문 CSV 파일을 찾을 수 없습니다: {e}")
    exit()

mapped_data = []

# 설문지 문항 키워드 매핑 (CSV 컬럼명 -> 코드용 변수명)
# 주의: 점수 해석 시 '신체적 노력', '불안정함'은 점수가 높을수록 부정적(나쁨)이고
# '접근성'은 점수가 높을수록 긍정적(좋음)입니다.
metric_keyword_map = {
    '신체적 노력': 'Physical Effort',   # Lower is better
    '접근성': 'Accessibility',       # Higher is better
    '그립 안정성': 'Grip Instability'   # Question asks about instability (Higher = Worse)
}

# 질문 번호(4,5,6)와 순서 인덱스(0,1,2) 매핑
ordinal_map_q = {4: 0, 5: 1, 6: 2}

print("🔄 설문 데이터 매핑 중...")

for idx, row in df_raw.iterrows():
    # '1. 성함' 컬럼 사용
    name = str(row.get('1. 성함', '')).strip()

    if not name or name not in participant_orders:
        if name: print(f"⚠️ 경고: 참가자 '{name}'의 로그(JSON)를 찾을 수 없어 제외합니다.")
        continue

    order = participant_orders[name] # 예: ['fixed', 'adaptive', 'bottom-right']

    p_data = {'Participant': name}

    # 1. 주관적 점수 매핑 (Q4~Q6)
    for col in df_raw.columns:
        # 컬럼명이 "4-1.", "5-2." 등으로 시작하는지 확인
        first_part = str(col).split('-')[0] # '4', '5', '6' 추출

        if first_part in ['4', '5', '6']:
            try:
                q_num = int(first_part)
                order_idx = ordinal_map_q[q_num] # 0, 1, 2
                condition = order[order_idx]     # 해당 순서의 조건명

                # 어떤 지표인지 확인
                for keyword, metric_name in metric_keyword_map.items():
                    if keyword in col:
                        score = row[col]
                        p_data[f'{condition}_{metric_name}'] = score
                        break
            except:
                continue

    # 2. 선호도 순위 매핑 (Q7)
    # 값 예시: "첫 번째", "두 번째"
    def map_val_to_cond(val, order_list):
        val_str = str(val)
        if '첫 번째' in val_str: return order_list[0]
        if '두 번째' in val_str: return order_list[1]
        if '세 번째' in val_str: return order_list[2]
        return 'Unknown'

    for col in df_raw.columns:
        if '7. [종합 순위]' in col:
            val = row[col]
            cond_name = map_val_to_cond(val, order)

            if '[1순위]' in col:
                p_data['Most_Preferred'] = cond_name
            elif '[2순위]' in col:
                p_data['Second_Preferred'] = cond_name
            elif '[3순위]' in col:
                p_data['Least_Preferred'] = cond_name

    mapped_data.append(p_data)

df_mapped = pd.DataFrame(mapped_data)

# ==========================================
# 4. 분석 및 시각화
# ==========================================

if df_mapped.empty:
    print("❌ 매핑된 데이터가 없습니다. 이름 매칭을 확인하세요.")
    exit()

# 4-1. 조건별 평균 점수 비교 그래프
print("\n📊 조건별 주관적 평가 점수 비교")
plot_data = []

conditions = ['fixed', 'adaptive', 'bottom-right']
metrics = ['Physical Effort', 'Accessibility', 'Grip Instability']

for cond in conditions:
    for met in metrics:
        col_name = f'{cond}_{met}'
        if col_name in df_mapped.columns:
            avg_score = pd.to_numeric(df_mapped[col_name], errors='coerce').mean()
            plot_data.append({
                'Condition': cond,
                'Metric': met,
                'Score': avg_score
            })

df_plot = pd.DataFrame(plot_data)

plt.figure(figsize=(12, 6))
sns.barplot(x='Metric', y='Score', hue='Condition', data=df_plot, palette='viridis')
plt.title('Subjective User Ratings (Mapped Results)')
plt.ylabel('Average Score (7-point scale)')
plt.ylim(0, 7.5) # 7점 척도 가정
plt.legend(title='Condition')
plt.grid(axis='y', alpha=0.3)

# 그래프 해석 가이드 추가
plt.text(0, -1.5, "* Physical Effort / Grip Instability: 낮을수록 좋음 (Lower is Better)\n* Accessibility: 높을수록 좋음 (Higher is Better)",
         ha='left', fontsize=10, color='gray')

plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, 'Fig7_Mapped_Ratings.png'), dpi=300)
print("✅ Fig7_Mapped_Ratings.png 저장 완료")

# 4-2. 가장 선호하는 UI (Pie Chart)
print("\n📊 선호도 분석 (1순위)")
if 'Most_Preferred' in df_mapped.columns:
    pref_counts = df_mapped['Most_Preferred'].value_counts()
    print(pref_counts)

    plt.figure(figsize=(7, 7))
    plt.pie(pref_counts, labels=pref_counts.index, autopct='%1.1f%%',
            colors=sns.color_palette('pastel'), startangle=90)
    plt.title('Most Preferred UI (1st Choice)')
    plt.savefig(os.path.join(RESULT_DIR, 'Fig6_Mapped_Preference.png'), dpi=300)
    print("✅ Fig6_Mapped_Preference.png 저장 완료")
else:
    print("⚠️ 선호도 데이터를 찾을 수 없습니다.")

print("\n🚀 순서 기반 매핑 분석 완료. 결과 폴더를 확인하세요.")