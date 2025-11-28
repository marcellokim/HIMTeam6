import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
DATA_PATH = './results/processed_data.csv'
RESULT_DIR = './results'

# 한글 폰트 설정 (Mac: AppleGothic, Windows: Malgun Gothic)
import platform
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

print("🔄 데이터 로드 및 분석 시작...")
df = pd.read_csv(DATA_PATH)

# ==========================================
# 2. 통계 검정 함수 정의
# ==========================================
def perform_stats(data, metric, group_col='Condition'):
    print(f"\n[{metric} 분석]")
    conditions = data[group_col].unique()

    # 기술 통계
    desc = data.groupby(group_col)[metric].agg(['mean', 'std', 'median'])
    print(desc)

    # 피험자별 평균 데이터 생성 (대응 표본 검정을 위해)
    df_pivot = data.pivot_table(index='Participant', columns=group_col, values=metric, aggfunc='mean')

    # 1. 정규성 검정 (Shapiro-Wilk)
    print("- 정규성 검정 (p < 0.05면 정규성 위반):")
    for cond in conditions:
        stat, p = stats.shapiro(df_pivot[cond])
        print(f"  {cond}: p={p:.4f}")

    # 2. 통계 검정 (Wilcoxon Signed-Rank Test - 비모수 검정, N=14 소표본에 적합)
    print("- Wilcoxon Signed-Rank Test (대응 표본):")
    pairs = [('fixed', 'adaptive'), ('adaptive', 'bottom-right')]

    stats_results = []
    for c1, c2 in pairs:
        stat, p = stats.wilcoxon(df_pivot[c1], df_pivot[c2])
        stars = "*" if p < 0.05 else "ns"
        if p < 0.01: stars = "**"
        if p < 0.001: stars = "***"

        print(f"  {c1} vs {c2}: Statistic={stat:.1f}, p={p:.4f} ({stars})")
        stats_results.append({'pair': f"{c1}-{c2}", 'p': p})

    return stats_results

# ==========================================
# 3. 핵심 분석 실행 (RQ1: Efficiency)
# ==========================================
print("\n" + "="*40)
print("📊 1. 효율성 분석 (Efficiency)")
print("="*40)

# 3-1. Search Time (속도)
perform_stats(df, 'SearchTime')

# 3-2. Offset (정확도) - 여기가 승부처입니다!
perform_stats(df, 'Offset')


# ==========================================
# 4. 학습 효과 분석 (Learning Effect)
# ==========================================
print("\n" + "="*40)
print("📈 2. 학습 효과 분석 (Trial 1 vs 5)")
print("="*40)

# 회차별, 조건별 평균 계산
learning_curve = df.pivot_table(index='Trial_Order', columns='Condition', values='SearchTime')
print(learning_curve)


# ==========================================
# 5. 개인화 필요성 분석 (RQ3: Personalization)
# ==========================================
print("\n" + "="*40)
print("🎯 3. 개인화 필요성 분석 (Radius vs Performance)")
print("="*40)

# 피험자별 Radius와 성능 이득(Time Saving) 계산
# Time Saving = (Fixed Time) - (Adaptive Time)
# Radius가 작을수록(손이 작을수록) Saving이 큰지 확인 (음의 상관관계 예상)
df_perf = df.pivot_table(index=['Participant', 'Reachable_Radius'], columns='Condition', values='SearchTime').reset_index()
df_perf['Time_Saving'] = df_perf['fixed'] - df_perf['adaptive']
df_perf['Accuracy_Gain'] = df.pivot_table(index='Participant', columns='Condition', values='Offset')['fixed'] - \
                           df.pivot_table(index='Participant', columns='Condition', values='Offset')['adaptive']

corr_time, p_time = stats.pearsonr(df_perf['Reachable_Radius'], df_perf['Time_Saving'])
corr_acc, p_acc = stats.pearsonr(df_perf['Reachable_Radius'], df_perf['Accuracy_Gain'])

print(f"- Radius vs Time Saving 상관계수: r={corr_time:.3f}, p={p_time:.4f}")
print(f"- Radius vs Accuracy Gain 상관계수: r={corr_acc:.3f}, p={p_acc:.4f}")


# ==========================================
# 6. 논문용 그래프 생성 및 저장
# ==========================================
print("\n🎨 그래프 생성 중...")
sns.set(style="whitegrid", font_scale=1.1)
# 폰트 재설정 (Seaborn style 적용 후 깨짐 방지)
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')

# Graph 1: Search Time & Offset (Bar Plot)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sns.barplot(x='Condition', y='SearchTime', data=df, errorbar='se', ax=axes[0],
            order=['fixed', 'adaptive', 'bottom-right'], palette='Blues')
axes[0].set_title('Average Search Time (ms)')
axes[0].set_ylabel('Time (ms)')

sns.barplot(x='Condition', y='Offset', data=df, errorbar='se', ax=axes[1],
            order=['fixed', 'adaptive', 'bottom-right'], palette='Reds')
axes[1].set_title('Touch Accuracy (Offset Distance)')
axes[1].set_ylabel('Offset (pixels)')
axes[1].set_ylim(0, None)  # 0부터 시작

plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, 'Fig1_Efficiency.png'), dpi=300)
print("✅ Fig1_Efficiency.png 저장 완료")

# Graph 2: Learning Curve (Line Plot)
plt.figure(figsize=(10, 6))
sns.lineplot(x='Trial_Order', y='SearchTime', hue='Condition', data=df,
             style='Condition', markers=True, dashes=False, palette='deep')
plt.title('Learning Effect: Search Time across Trials')
plt.ylabel('Search Time (ms)')
plt.xlabel('Trial Order')
plt.xticks([1, 2, 3, 4, 5])
plt.savefig(os.path.join(RESULT_DIR, 'Fig2_LearningCurve.png'), dpi=300)
print("✅ Fig2_LearningCurve.png 저장 완료")

# Graph 3: Correlation Scatter Plot (Personalization)
plt.figure(figsize=(8, 6))
sns.regplot(x='Reachable_Radius', y='Time_Saving', data=df_perf, color='green', scatter_kws={'s':100})
plt.title(f'Correlation: Reachable Radius vs. Adaptive Benefit\n(r={corr_time:.2f}, p={p_time:.3f})')
plt.xlabel('Thumb Reachable Radius (pixels)')
plt.ylabel('Time Saved by Adaptive UI (ms)')
plt.axhline(0, color='gray', linestyle='--')
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(RESULT_DIR, 'Fig3_Personalization.png'), dpi=300)
print("✅ Fig3_Personalization.png 저장 완료")

# Graph 4: Touch Position Scatter (Spatial Consistency)
# 버튼 중심을 (0,0)으로 가정하고 오차 분포 시각화는
# 오프셋 거리만 있으므로, 여기서는 오프셋 분포(Violin)로 대체하여 정밀함을 강조
plt.figure(figsize=(10, 6))
sns.violinplot(x='Condition', y='Offset', data=df,
               order=['fixed', 'adaptive', 'bottom-right'], palette='Pastel1', inner='quartile')
plt.title('Distribution of Touch Offsets (Precision Analysis)')
plt.ylabel('Offset Distance from Button Center (px)')
plt.savefig(os.path.join(RESULT_DIR, 'Fig4_Offset_Distribution.png'), dpi=300)
print("✅ Fig4_Offset_Distribution.png 저장 완료")

print("\n🚀 모든 분석이 완료되었습니다. 'results' 폴더를 확인하세요.")