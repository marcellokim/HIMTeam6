import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
# 파일 경로 (실제 파일 위치에 맞게 수정하세요)
SURVEY_PATH = './사후 설문 정리.csv'
PROCESS_PATH = './results/processed_data.csv'
RESULT_DIR = './results'

# 한글 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

print("🔄 데이터 로드 중...")
try:
    # 인코딩 에러 방지를 위해 engine='python' 사용
    df_survey = pd.read_csv(SURVEY_PATH)
    df_process = pd.read_csv(PROCESS_PATH)
except Exception as e:
    print(f"❌ 데이터 로드 실패: {e}")
    exit()

# ==========================================
# 2. 데이터 전처리 (순위 데이터 생성)
# ==========================================
print("🔄 데이터 매핑 중...")

# 2-1. 참가자별 실험 순서 추출 (processed_data.csv 이용)
# 예: 홍길동 -> ['fixed', 'adaptive', 'bottom-right']
condition_orders = {}
for p in df_process['Participant'].unique():
    # 참가자의 데이터를 Trial_Order 순으로 정렬하여 조건 추출
    p_data = df_process[df_process['Participant'] == p].sort_values('Trial_Order')
    # 중복 제거하면서 순서 유지
    conds = []
    for c in p_data['Condition']:
        if c not in conds:
            conds.append(c)
    condition_orders[p] = conds

# 2-2. 설문 응답을 실제 조건으로 변환하여 순위 데이터프레임 생성
rank_rows = []
col_name = '1. 성함'
col_1st = '7. [종합 순위] 실제 실생활에서 사용하고 싶은 방식을 순서대로 선택해주세요. [1순위]'
col_2nd = '7. [종합 순위] 실제 실생활에서 사용하고 싶은 방식을 순서대로 선택해주세요. [2순위]'
col_3rd = '7. [종합 순위] 실제 실생활에서 사용하고 싶은 방식을 순서대로 선택해주세요. [3순위]'

for idx, row in df_survey.iterrows():
    name = row[col_name]
    if name not in condition_orders:
        continue

    order = condition_orders[name] # 실험 순서 리스트

    # 설문지의 "첫 번째", "두 번째"를 실제 조건명으로 매핑
    map_dict = {'첫 번째': order[0], '두 번째': order[1], '세 번째': order[2]}

    choice_1 = map_dict.get(row[col_1st]) # 1위로 뽑은 조건
    choice_2 = map_dict.get(row[col_2nd]) # 2위로 뽑은 조건
    choice_3 = map_dict.get(row[col_3rd]) # 3위로 뽑은 조건

    # 랭크 딕셔너리 생성 (Condition: Rank)
    ranks = {}
    if choice_1: ranks[choice_1] = 1
    if choice_2: ranks[choice_2] = 2
    if choice_3: ranks[choice_3] = 3

    rank_rows.append({
        'Participant': name,
        'fixed': ranks.get('fixed'),
        'adaptive': ranks.get('adaptive'),
        'bottom-right': ranks.get('bottom-right')
    })

df_rank = pd.DataFrame(rank_rows)
print(f"✅ 총 {len(df_rank)}명의 순위 데이터 생성 완료")

# ==========================================
# 3. 프리드먼 검정 및 사후 분석
# ==========================================
print("\n📊 통계 분석 결과")
print("="*40)

# 3-1. Friedman Test
stat, p_value = stats.friedmanchisquare(
    df_rank['fixed'],
    df_rank['adaptive'],
    df_rank['bottom-right']
)

print(f"[Friedman Test]")
print(f"- Chi-square: {stat:.3f}")
print(f"- P-value: {p_value:.4f}")

mean_ranks = df_rank[['fixed', 'adaptive', 'bottom-right']].mean()
print("\n[Mean Ranks] (낮을수록 선호도 높음)")
print(mean_ranks.sort_values())

# 3-2. Post-hoc Analysis (Wilcoxon with Bonferroni)
if p_value < 0.05:
    print("\n[Post-hoc: Wilcoxon Signed-Rank Test]")
    print("(Bonferroni corrected alpha = 0.05 / 3 = 0.017)")

    pairs = [('fixed', 'adaptive'), ('fixed', 'bottom-right'), ('adaptive', 'bottom-right')]
    sig_pairs = []

    for c1, c2 in pairs:
        w_stat, w_p = stats.wilcoxon(df_rank[c1], df_rank[c2])
        # Bonferroni correction 적용한 유의성 판단
        is_sig = w_p < (0.05 / 3)
        star = "**" if is_sig else "ns"
        print(f"- {c1} vs {c2}: p={w_p:.4f} ({star})")

        if is_sig:
            sig_pairs.append((c1, c2, w_p))
else:
    print("\n👉 프리드먼 검정 결과가 유의하지 않아 사후 검정을 생략합니다.")

# ==========================================
# 4. 시각화 (Mean Rank Bar Plot)
# ==========================================
print("\n🎨 그래프 생성 중...")
plt.figure(figsize=(8, 6))
sns.set(style="whitegrid", font_scale=1.1)
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')

# 데이터 변환 (Plot용)
plot_data = pd.DataFrame({
    'Condition': ['Fixed', 'Adaptive', 'Bottom-Right'],
    'Mean Rank': [mean_ranks['fixed'], mean_ranks['adaptive'], mean_ranks['bottom-right']]
})

# 막대 그래프 그리기 (순서: Fixed, Adaptive, Bottom-Right)
ax = sns.barplot(x='Condition', y='Mean Rank', data=plot_data,
                 order=['Fixed', 'Adaptive', 'Bottom-Right'], palette='viridis')

# 그래프 꾸미기
ax.set_title('User Preference Rankings (Lower is Better)', fontsize=14, pad=20)
ax.set_ylabel('Mean Rank (1=Best, 3=Worst)')
ax.set_ylim(1, 3.5) # Y축 범위 조정
ax.set_yticks([1, 1.5, 2, 2.5, 3])

# 막대 위에 값 표시
for i, v in enumerate(plot_data['Mean Rank']):
    # 원래 순서대로 매핑: Fixed(0), Adaptive(1), Bottom-Right(2)
    # plot_data의 순서가 섞일 수 있으므로 조건에 맞춰 인덱싱
    val = plot_data.set_index('Condition').loc[['Fixed', 'Adaptive', 'Bottom-Right'][i], 'Mean Rank']
    ax.text(i, val + 0.05, f"{val:.2f}", ha='center', fontweight='bold')

# 유의성 표시 (Significant pairs) - 수동 추가 (예시: Fixed vs Adaptive가 유의하다면)
# 실제 p-value 결과에 따라 이 부분을 조정해서 쓰세요.
# 여기서는 코드가 자동으로 p-value를 확인하여 그립니다.
if p_value < 0.05:
    # Fixed vs Adaptive (인덱스 0과 1)
    # 실제 통계 결과 변수(sig_pairs)를 활용
    for pair in sig_pairs:
        if 'fixed' in pair and 'adaptive' in pair:
            # Fixed(0) - Adaptive(1) 사이 선 긋기
            x1, x2 = 0, 1
            y, h = 2.8, 0.1
            ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.5, c='k')
            ax.text((x1+x2)*.5, y+h, "**", ha='center', va='bottom', color='k', fontsize=12)

plt.tight_layout()
save_path = os.path.join(RESULT_DIR, 'Fig8_Preference_Ranks.png')
plt.savefig(save_path, dpi=300)
print(f"✅ 결과 그래프 저장 완료: {save_path}")