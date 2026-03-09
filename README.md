# ScR-screener
Title・abstractスクリーニングの補助

このプロジェクトは、スコーピングレビュー（Scoping Review）における論文のタイトルとアブストラクトのスクリーニングを、ローカルAI環境（Ollama）を用いて自動化するためのツール群です。

## 概要

APIの利用料金を気にすることなく、数千件規模の文献データを対象に包含基準・除外基準（Include/Exclude基準）と照らし合わせ、自動的かつ連続的に1〜5段階のスクリーニング評価と除外理由のコメント生成を行います。
途中で処理を中断・再開しても、重複して同じ論文を評価しない安全設計となっています。

## 構成ファイル

- `Articles.csv`: 検索データベース（Web of Scienceなど）からエクスポートした生の文献データ（入力元）。
- `Criteria.csv`: 評価基準。各列に定義されたInclude基準とExclude基準が、AIへの評価プロンプトとして利用されます。
- `extract_columns.py`: `Articles.csv` からスクリーニングに必要な「Article Title」と「Abstract」の2つの列のみを抽出し、`Articles_cleaned.csv` を生成する前処理スクリプト。
- `run_local_screening.py`: ローカル構築されたAI環境（Ollama）を用いて、クリーンアップされた文献データの評価を自動で実行するメインスクリプト。結果は1件ごとに自動保存されます。
- `Prompt.md`: AIにスクリーニングの指示を出すための基本プロンプトの設計書（AIチャットや他の環境で個別実行する際に参照します）。

## 実行環境

本システムは、ローカル環境で無料の高性能LLMを稼働させるために **Ollama** を利用します。また、Pythonの標準ライブラリ（`csv`, `json`, `urllib`など）のみで動作するように設計されており、**特別な外部ライブラリ（`pip install`が必要なもの）への依存はありません**。

### 必要なソフトウェア

1. **Python 3.x**
2. **Ollama** (ローカルLLM実行環境)

## セットアップ手順

### 1. Ollamaのインストールとモデルの準備

以下のいずれかの方法でOllama（Mac向け）をインストールします。

**方法1: 公式サイトからインストーラーをダウンロード（推奨）**
1. [Ollama-darwin.zip をダウンロードする](https://ollama.com/download/Ollama-darwin.zip)
2. ZIPを解凍し、中身のOllamaアプリを起動しセットアップを完了させます（メニューバーにラマのアイコンが表示されれば起動状態です）。

**方法2: Homebrewでインストール**
```bash
brew install ollama
brew services start ollama
```

### 2. 利用するAIモデルのダウンロード

ターミナルを開き、以下のコマンドでお好みのローカルLLM（ここではデフォルト設定の `llama3.1`）をダウンロードします（約4.7GB）。
*※ダウンロードには数分かかります。プログレスバーが100%になるのをお待ちください。*

```bash
ollama pull llama3.1
```

## スクリーニングの実行方法

### Step 1: データの準備
入力元の文献データ（`Articles.csv`）と評価基準（`Criteria.csv`）を同じディレクトリに配置します。

### Step 2: 前処理スクリプトの実行
タイトルとアブストラクトの必要な列のみを抽出します。
```bash
python3 extract_columns.py
```
*-> 成功すると `Articles_cleaned.csv` が生成されます。*

### Step 3: 自動スクリーニングの実行
ローカルAIを呼び出し、自動評価を開始します。
```bash
python3 run_local_screening.py
```

実行中はターミナルに以下のような進捗が表示されます。
```
[1/1044] 処理中: Large Language Model Failures in Higher Education...
[2/1044] 処理中: Can artificial intelligence improve the readability...
...
```

**自動再開機能:**
実行中に `Ctrl+C` を押すかPCの電源を落として処理を中断した場合でも、次回 `python3 run_local_screening.py` を再実行すれば、**未評価の文献から自動で再開**されます。

## 出力結果 (`screening_results.csv`)

スクリーニングされた結果は、即座に1件ずつ `screening_results.csv` に追記されます。以下のカラムが含まれます。

- **論文名**: タイトル
- **アブストラクト**: 要約テキスト
- **適切度(1~5)**: 5が完全に適格、1が完全に不適格
- **コメント**: 判断の根拠となったCriteriaの基準と理由（不適格または保留の場合）
