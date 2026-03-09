import csv
import sys
import os

def extract_columns(input_file, output_file, columns):
    try:
        # utf-8-sigを使用して、BOM付きのCSVファイルにも対応します
        with open(input_file, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            
            # ヘッダーの存在確認と必要なカラムが含まれているかの検証
            if not reader.fieldnames:
                print(f"エラー: {input_file} が空か、ヘッダーが存在しません。")
                sys.exit(1)
                
            missing_columns = [col for col in columns if col not in reader.fieldnames]
            if missing_columns:
                print(f"エラー: {input_file} に以下のカラムが見つかりません: {', '.join(missing_columns)}")
                print(f"利用可能なカラム: {', '.join(reader.fieldnames)}")
                sys.exit(1)
            
            with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=columns)
                writer.writeheader()
                
                for row in reader:
                    # 指定されたカラムのみを抽出します（データが存在しない場合は空文字）
                    extracted_row = {col: row.get(col, '') for col in columns}
                    writer.writerow(extracted_row)
                    
        print(f"抽出が完了しました。結果は {output_file} に保存されています。")

    except FileNotFoundError:
        print(f"エラー: {input_file} が見つかりません。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(current_dir, 'Articles.csv')
    output_csv = os.path.join(current_dir, 'Articles_cleaned.csv')
    
    target_columns = ['Article Title', 'Abstract']
    
    extract_columns(input_csv, output_csv, target_columns)
