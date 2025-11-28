import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import json
import glob
import math

# 1. 데이터 로드 (JSON에서 직접 좌표 데이터 추출 필요)
DATA_DIR = './data'
RESULT_DIR = './results'

# 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

def extract_touch_coordinates(data_dir):
    json_pattern = os.path.join(data_dir, '*.json')
    file_list = glob.glob(json_pattern)

    touch_points = []

    for file_path in file_list:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for exp in data['experiments']:
            condition = exp['condition']
            for trial in exp['trials']:
                btn_pos = trial['buttonPosition']
                touch_pos = trial.get('buttonTouchPosition')

                if touch_pos:
                    # 버튼 중심을 (0,0)으로 기준 잡기 (Relative Coordinates)
                    # dx: 터치점 - 버튼중심
                    dx = touch_pos['x'] - btn_pos['x']
                    dy = touch_pos['y'] - btn_pos['y']

                    # 버튼 크기 (반지름 약 40px 가정, 시각화용)
                    touch_points.append({
                        'Condition': condition,
                        'Delta_X': dx,
                        'Delta_Y': dy
                    })

    return pd.DataFrame(touch_points)

print("🔄 좌표 데이터 추출 중...")
df_coords = extract_touch_coordinates(DATA_DIR)

# 2. 히트맵 시각화 (KDE Plot)
print("🎨 터치 히트맵 생성 중...")

plt.figure(figsize=(15, 5))
conditions = ['fixed', 'adaptive', 'bottom-right']
colors = {'fixed': 'Reds', 'adaptive': 'Greens', 'bottom-right': 'Blues'}
titles = {
    'fixed': 'Fixed UI (Top-Right)',
    'adaptive': 'Adaptive UI (Personalized)',
    'bottom-right': 'Bottom-Right (Randomized)'
}

for i, cond in enumerate(conditions):
    plt.subplot(1, 3, i+1)

    subset = df_coords[df_coords['Condition'] == cond]

    # 중심점(0,0) 표시
    plt.scatter(0, 0, s=200, c='black', marker='+', label='Button Center')

    # 버튼 영역 표시 (반지름 40px 원)
    circle = plt.Circle((0, 0), 40, color='gray', fill=False, linestyle='--', linewidth=2)
    plt.gca().add_patch(circle)

    # 밀도 그래프 그리기 (터치가 집중된 곳)
    # fill=True, levels=10 등으로 등고선 표현
    try:
        sns.kdeplot(
            data=subset, x='Delta_X', y='Delta_Y',
            cmap=colors[cond], fill=True, alpha=0.7, thresh=0.1
        )
        # 실제 점들도 작게 찍어주기 (산포도)
        plt.scatter(subset['Delta_X'], subset['Delta_Y'], s=10, c='black', alpha=0.2)
    except:
        print(f"⚠️ {cond} 조건의 데이터가 너무 적거나 퍼져있어서 KDE를 그릴 수 없습니다. 산포도만 그립니다.")
        plt.scatter(subset['Delta_X'], subset['Delta_Y'], s=20, c='blue', alpha=0.5)

    plt.title(titles[cond], fontsize=14, fontweight='bold')
    plt.xlim(-100, 100)  # 버튼 중심 기준 좌우 100px
    plt.ylim(-100, 100)  # 버튼 중심 기준 상하 100px
    plt.xlabel('Horizontal Offset (px)')
    if i == 0:
        plt.ylabel('Vertical Offset (px)')
    else:
        plt.ylabel('')

    plt.axvline(0, color='gray', linestyle=':', alpha=0.5)
    plt.axhline(0, color='gray', linestyle=':', alpha=0.5)
    plt.grid(True, alpha=0.2)

plt.tight_layout()
save_path = os.path.join(RESULT_DIR, 'Fig5_Touch_Heatmap.png')
plt.savefig(save_path, dpi=300)
print(f"✅ 히트맵 저장 완료: {save_path}")