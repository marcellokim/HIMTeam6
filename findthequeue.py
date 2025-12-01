import json
import glob
import os

# ==========================================
# 설정: JSON 파일들이 들어있는 폴더 경로
# ==========================================
JSON_DIR = './data'

def check_experiment_orders():
    # 폴더 내 모든 .json 파일 찾기
    json_files = glob.glob(os.path.join(JSON_DIR, '*.json'))

    print(f"📂 총 {len(json_files)}개의 파일을 찾았습니다.\n")
    print("📋 [참가자별 실험 진행 순서]")
    print("=" * 50)

    for file_path in sorted(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 이름 추출
                name = data['participant']['name'].strip()

                # 실험 순서 추출 (experiments 리스트에 저장된 순서가 실제 수행 순서임)
                # 리스트 컴프리헨션으로 조건명만 뽑아내기
                orders = [exp['condition'] for exp in data['experiments']]

                # 보기 좋게 출력 (예: 홍길동: Fixed -> Adaptive -> Bottom-Right)
                order_str = " -> ".join(orders)
                print(f"👤 {name}: {order_str}")

        except Exception as e:
            print(f"⚠️ 에러 발생 ({os.path.basename(file_path)}): {e}")

    print("=" * 50)

if __name__ == "__main__":
    check_experiment_orders()