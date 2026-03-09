import csv
import json
import urllib.request
import urllib.error
import time
import os
import sys

# 【設定】
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama4" # ここはダウンロードしたモデル名に合わせて変更可能です（例: "qwen2.5", "gemma2" など）
INPUT_FILE = "Articles_cleaned.csv"
OUTPUT_FILE = "screening_results.csv"
CRITERIA_FILE = "Criteria.csv"

def read_criteria(file_path):
    criteria_text = ""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            criteria_text = f.read()
    except Exception as e:
        print(f"[{CRITERIA_FILE}] の読み込みに失敗しました: {e}")
        sys.exit(1)
    return criteria_text

def get_already_processed_titles(output_path):
    titles = set()
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    titles.add(row.get("論文名", ""))
        except Exception as e:
            print(f"ファイルの読み込みエラー: {e}")
    return titles

def evaluate_article_with_ollama(title, abstract, criteria_text):
    system_prompt = f"""あなたはスコーピングレビューにおける論文のタイトルとアブストラクトのスクリーニングを行う、専門的なAIリサーチャーです。
以下のInclude/Exclude基準に基づいて、提供される論文を評価してください。

【基準】
{criteria_text}

【適切度の評価基準】
- 5: 完全に適格（Include基準を満たし、Exclude基準に一切該当しない）
- 4: おそらく適格（情報がわずかに不足しているが、適格の可能性が高い）
- 3: 判断保留（タイトルとアブストラクトのみでは情報が不足しており、フルテキストによる判断が必要）
- 2: おそらく不適格（Exclude基準に該当する、またはInclude基準を満たさない可能性が高い）
- 1: 完全に不適格（明確にExclude基準に該当する、または明確にInclude基準を満たさない）

【出力フォーマット】
必ず以下のJSON形式でのみ出力してください。それ以外のテキストは一切含めないでください。
{{
  "score": (1〜5の数値。例: 5),
  "comment": "(適切ではない・保留の理由。Criteriaのどの基準に該当するかを明記。適格な場合は'完全に適格'と記載)"
}}"""

    user_prompt = f"論文名: {title}\nアブストラクト: {abstract}\n\nこの論文の適切度を1〜5で評価し、理由をJSONで出力してください。"

    data = {
        "model": MODEL_NAME,
        "prompt": user_prompt,
        "system": system_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0 # より決定論的な回答を得るために0
        }
    }

    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                response_text = res_data.get("response", "{}")
                
                # JSONとしてパースできるか確認
                result_json = json.loads(response_text)
                
                score = result_json.get("score")
                comment = result_json.get("comment", "")
                
                # scoreが数値として正常に取れなかった場合のフォールバック
                if not isinstance(score, (int, float)):
                    try:
                        score = int(score)
                    except:
                        score = 3
                        comment = f"（パースエラー）{comment} | 元の出力: {response_text}"
                
                return score, comment

        except urllib.error.URLError as e:
            print(f"Ollama APIへの接続に失敗しました（再試行 {attempt + 1}/{max_retries}）: {e}")
            time.sleep(2)
        except json.JSONDecodeError as e:
            print(f"JSONパースエラー（再試行 {attempt + 1}/{max_retries}）: {e}\n出力: {response_text}")
            time.sleep(2)
        except Exception as e:
            print(f"予期せぬエラー（再試行 {attempt + 1}/{max_retries}）: {e}")
            time.sleep(2)
            
    return 3, "エラー: 何度か試行しましたがAIの回答を正常に取得・解析できませんでした。"

def main():
    print(f"--- ローカルAI ({MODEL_NAME}) を使用した一括スクリーニングを開始します ---")
    
    # 接続確認
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
        print("✓ Ollamaの起動を確認しました。")
    except Exception as e:
        print("✗ Ollamaに接続できません。アプリを起動しているか確認してください。")
        sys.exit(1)

    criteria_text = read_criteria(CRITERIA_FILE)
    processed_titles = get_already_processed_titles(OUTPUT_FILE)
    
    articles = []
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            articles = list(reader)
    except Exception as e:
        print(f"[{INPUT_FILE}] の読み込みに失敗しました: {e}")
        sys.exit(1)

    print(f"全 {len(articles)} 件中、既に {len(processed_titles)} 件が処理済みです。")
    remaining = [a for a in articles if a.get("Article Title", "") not in processed_titles]
    print(f"残り {len(remaining)} 件を処理します...")
    
    # CSVの追記モード
    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["論文名", "アブストラクト（省略可）", "適切度(1~5)", "コメント"])
            
        success_count = 0
        
        for i, article in enumerate(remaining, 1):
            title = article.get("Article Title", "")
            abstract = article.get("Abstract", "")
            
            # 空行・タイトル無しの行はスキップ
            if not title:
                continue
                
            print(f"[{i}/{len(remaining)}] 処理中: {title[:50]}...")
            
            score, comment = evaluate_article_with_ollama(title, abstract, criteria_text)
            
            # 結果を書き込みして即座にflushする（途中で強制終了しても安全なように）
            writer.writerow([title, abstract, score, comment])
            f.flush()
            
            success_count += 1

    print(f"\n--- 完了 ---")
    print(f"新たに {success_count} 件の評価が {OUTPUT_FILE} に追記されました！")

if __name__ == "__main__":
    main()
