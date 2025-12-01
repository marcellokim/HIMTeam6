import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
from math import pi

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
SURVEY_PATH = './사후 설문 정리.csv'  # 파일명 확인 필요
RESULT_DIR = './results'

# 한글 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

# 데이터 로드 (인코딩 문제 대응)
try:
    df = pd.read_csv(SURVEY_PATH, encoding='utf-8')
except:
    df = pd.read_csv(SURVEY_PATH, encoding='cp949')

print("🔄 설문 데이터 로드 완료")

# ==========================================
# 2. 데이터 전처리 (컬럼명 매핑)
# ==========================================
# 실제 CSV 컬럼명에 맞춰 키워드로 찾아서 매핑
cols = df.columns
metrics = {
    'Physical Effort': '신체적 노력',
    'Accessibility': '접근성',
    'Grip Instability': '그립 안정성'
}

# 분석할 데이터 구조 만들기
# {Metric_Name: DataFrame(rows=users, cols=conditions)}
analyzed_data = {}

for metric_eng, metric_kor in metrics.items():
    # 해당 키워드가 포함된 컬럼 찾기
    targets = [c for c in cols if metric_kor in c]

    # 조건별로 분류 (첫 번째=Fixed, 두 번째=Adaptive, 세 번째=Bottom-Right 아님! 순서 확인 필요)
    # 아까 processed_data.csv에서 얻은 'condition_orders'가 필요함.
    # 하지만 여기서는 설문지 컬럼 자체가 "4-1. 첫 번째 방식" 등으로 되어 있으므로,
    # 참가자별 실험 순서 정보를 매핑해야 함.
    pass

# 위의 복잡함을 피하기 위해, 이미 매핑된 파일(mapped_survey_data_check.csv)을 쓰거나
# 아니면 여기서 매핑 로직을 다시 구현해야 합니다.
# 사용자가 올린 'mapped_survey_data_check.csv'가 있다면 그걸 쓰는 게 베스트입니다.
# 여기서는 'mapped_survey_data_check.csv' 구조를 가정하고 작성합니다.

MAPPED_DATA_PATH = './results/mapped_survey_data_check.csv'
if os.path.exists(MAPPED_DATA_PATH):
    df_mapped = pd.read_csv(MAPPED_DATA_PATH)
else:
    # 매핑된 파일이 없으면 에러 (이전 단계에서 생성된 파일 사용 권장)
    print("❌ 'mapped_survey_data_check.csv' 파일이 필요합니다. (또는 파일명 수정)")
    exit()

# ==========================================
# 3. 프리드먼 검정 및 시각화 Loop
# ==========================================
metrics_cols = {
    'Physical Effort': ['fixed_Physical_Effort', 'adaptive_Physical_Effort', 'bottom-right_Physical_Effort'],
    'Accessibility': ['fixed_Accessibility', 'adaptive_Accessibility', 'bottom-right_Accessibility'],
    'Grip Instability': ['fixed_Grip_Instability', 'adaptive_Grip_Instability', 'bottom-right_Grip_Instability']
}

# 결과 저장용 리스트
radar_means = {'fixed': [], 'adaptive': [], 'bottom-right': []}
radar_labels = []

for metric, cols in metrics_cols.items():
    print(f"\n📊 [{metric}] 분석 결과 (1: 긍정/부정 확인 필요)")
    print("-" * 40)

    # 데이터 추출
    data = df_mapped[cols]
    data.columns = ['Fixed', 'Adaptive', 'Bottom-Right']

    # 평균 저장 (레이더 차트용)
    for cond in ['Fixed', 'Adaptive', 'Bottom-Right']:
        radar_means[cond.lower()].append(data[cond].mean())
    radar_labels.append(metric)

    # 1. 기술 통계
    print(data.describe().loc[['mean', 'std', '50%']])

    # 2. Friedman Test
    stat, p = stats.friedmanchisquare(data['Fixed'], data['Adaptive'], data['Bottom-Right'])
    print(f"  👉 Friedman Test: Chi2={stat:.3f}, p={p:.4f}")

    if p < 0.05:
        print("     (유의미한 차이 발견! 사후 검정 진행)")
        pairs = [('Fixed', 'Adaptive'), ('Adaptive', 'Bottom-Right'), ('Fixed', 'Bottom-Right')]
        for c1, c2 in pairs:
            w_stat, w_p = stats.wilcoxon(data[c1], data[c2])
            sig = "**" if w_p < 0.017 else ("*" if w_p < 0.05 else "ns")
            print(f"     - {c1} vs {c2}: p={w_p:.4f} ({sig})")

    # 3. Box Plot 시각화
    plt.figure(figsize=(6, 5))
    sns.boxplot(data=data, palette="Set3")
    plt.title(f'{metric} Score Distribution (1-7 Likert)')
    plt.ylabel('Score (Lower/Higher depends on metric)')
    plt.ylim(0.5, 7.5)
    plt.tight_layout()
    plt.savefig(f"{RESULT_DIR}/Fig_TLX_{metric.replace(' ', '_')}.png", dpi=300)
    print(f"  ✅ 그래프 저장 완료: Fig_TLX_{metric.replace(' ', '_')}.png")

# ==========================================
# 4. 레이더 차트 (종합 비교)
# ==========================================
print("\n🎨 종합 레이더 차트 생성 중...")

# 레이더 차트 데이터 준비
labels = list(metrics_cols.keys())
num_vars = len(labels)

# 각 축의 각도 계산
angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
angles += angles[:1]  # 닫힌 도형을 위해 첫 번째 각도 추가

plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)

# 축 그리기
plt.xticks(angles[:-1], labels, color='grey', size=12)

# Y축 설정 (1~7점)
ax.set_rlabel_position(0)
plt.yticks([1, 2, 3, 4, 5, 6, 7], ["1","2","3","4","5","6","7"], color="grey", size=7)
plt.ylim(0, 7)

# 데이터 플롯
colors = {'fixed': 'red', 'adaptive': 'green', 'bottom-right': 'blue'}
styles = {'fixed': ':', 'adaptive': '-', 'bottom-right': '--'}

for cond in ['fixed', 'adaptive', 'bottom-right']:
    values = radar_means[cond]
    values += values[:1]  # 닫힌 도형
    ax.plot(angles, values, linewidth=2, linestyle=styles[cond], label=cond, color=colors[cond])
    ax.fill(angles, values, color=colors[cond], alpha=0.1)

plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
plt.title('Comparison of Subjective Metrics (Radar Chart)', size=15, y=1.1)

plt.savefig(f"{RESULT_DIR}/Fig_TLX_Radar_Chart.png", dpi=300)
print(f"✅ 종합 레이더 차트 저장 완료: Fig_TLX_Radar_Chart.png")