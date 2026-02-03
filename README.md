# 労働安全衛生法令改正追跡システム

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

労働安全衛生関連法令の改正情報を自動的に収集・追跡するWebアプリケーション

![スクリーンショット](docs/screenshot.png)

## 📋 概要

このシステムは、労働安全衛生法やその関連法令の改正情報を厚生労働省などの公式サイトから自動収集し、改正プロセスごとに整理して表示します。企業の安全衛生担当者や社労士の方々が、法令改正を見逃さずにキャッチアップできるよう支援します。

## ✨ 特徴

### 📊 多様な情報源
- 厚生労働省 公式ページ
- e-Gov パブリックコメント
- 安全衛生情報センター
- e-Gov 法令検索

### 🔄 改正プロセスの可視化
1. **検討段階** - 審議会での議論
2. **パブリックコメント** - 意見募集
3. **国会審議中** - 法案審議
4. **公布済み** - 官報掲載
5. **施行予定** - 準備期間
6. **施行済み** - 法令適用開始

### 📋 対象法令（全25法令以上）
- 労働基準法
- 労働安全衛生法
- 19種類の安全規則（ボイラー、クレーン、化学物質など）
- その他関連法

## 🚀 クイックスタート

### 必要な環境
- Python 3.8以上
- Node.js 16以上（フロントエンド開発時）
- pip

### 1. リポジトリのクローン

```bash
git clone https://github.com/YOUR_USERNAME/safety-law-tracker.git
cd safety-law-tracker
```

### 2. バックエンドのセットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# APIサーバーの起動
python api_server.py
```

サーバーは `http://localhost:5000` で起動します。

### 3. フロントエンドのセットアップ

```bash
# 新規Reactプロジェクトを作成
npx create-react-app frontend
cd frontend

# 依存パッケージをインストール
npm install lucide-react

# safety-law-tracker-fixed.jsx を src/App.js にコピー
cp ../safety-law-tracker-fixed.jsx src/App.js

# Tailwind CSSのセットアップ（オプション）
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 開発サーバー起動
npm start
```

ブラウザで `http://localhost:3000` にアクセスできます。

## 📁 プロジェクト構成

```
safety-law-tracker/
├── README.md                           # このファイル
├── requirements.txt                    # Python依存パッケージ
├── .gitignore                         # Git除外設定
├── LICENSE                            # ライセンス
│
├── safety-law-tracker-fixed.jsx       # フロントエンド（React）
├── scraper.py                         # データ収集スクリプト
├── api_server.py                      # バックエンドAPIサーバー
│
└── docs/                              # ドキュメント
    └── screenshot.png                 # スクリーンショット
```

## 🔧 使い方

### Web UI

1. ブラウザで `http://localhost:3000` にアクセス
2. 検索ボックスで法令名や内容を検索
3. ステージフィルターで進捗状況を絞り込み
4. 各改正項目をクリックして詳細を表示
5. 公式ページやPDF資料へアクセス

### API エンドポイント

#### 改正情報一覧の取得
```bash
GET /api/revisions?stage=promulgated&search=化学物質
```

#### 特定改正情報の詳細
```bash
GET /api/revision/<revision_id>
```

#### 統計情報
```bash
GET /api/stats
```

#### 手動更新
```bash
POST /api/refresh
```

### スクリプトの直接実行

```bash
# データ収集のみ実行
python scraper.py
```

## 🤝 コントリビューション

Pull Requestを歓迎します！

1. このリポジトリをFork
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにPush (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 📝 開発ロードマップ

- [x] 基本的なスクレイピング機能
- [x] REST API
- [x] フロントエンドUI
- [x] 自動更新スケジューラー
- [ ] e-Gov API連携
- [ ] メール通知機能
- [ ] データベース保存
- [ ] Docker対応
- [ ] CI/CD設定

## ⚠️ 注意事項

### スクレイピングについて
- サーバーに負荷をかけないよう、リクエスト間隔を空けています
- robots.txtを遵守してください
- 商用利用の場合は各サイトの利用規約を確認してください

### データの正確性
- 自動収集したデータは参考情報です
- **重要な情報は必ず公式サイトで確認してください**

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## 👤 作成者

**Hayato**

## 🙏 謝辞

- 厚生労働省
- 安全衛生情報センター
- e-Gov

## 📞 サポート

問題が発生した場合は、[Issues](https://github.com/YOUR_USERNAME/safety-law-tracker/issues)で報告してください。

---

**注意**: このツールは情報提供を目的としています。法的判断が必要な場合は、専門家にご相談ください。

### 📊 情報源
- 厚生労働省 公式ページ
- e-Gov パブリックコメント
- 安全衛生情報センター
- e-Gov 法令検索
- 官報情報検索サービス

### 🔄 改正プロセスの可視化
1. **パブリックコメント募集中** - 意見募集期間とリンク
2. **審議中** - 国会での審議状況
3. **公布済み** - 公布日と施行予定日
4. **施行予定** - 施行までのカウントダウン
5. **施行済み** - 施行日の記録

### 📋 対象法令（全25法令）
- 基本法（労働基準法、労働安全衛生法など）
- 施行令・規則（19種類の安全規則）
- その他関連法

## システム構成

```
safety-law-tracker/
├── safety-law-tracker-enhanced.jsx  # フロントエンド（React）
├── scraper.py                       # データ収集スクリプト
├── api_server.py                    # バックエンドAPIサーバー
├── requirements.txt                 # Python依存パッケージ
└── README.md                        # このファイル
```

## セットアップ

### 1. 必要な環境
- Python 3.8以上
- Node.js 16以上（フロントエンド開発時）
- pip（Pythonパッケージマネージャー）

### 2. Pythonパッケージのインストール

```bash
pip install flask flask-cors beautifulsoup4 requests apscheduler
```

または requirements.txt から：

```bash
pip install -r requirements.txt
```

### 3. APIサーバーの起動

```bash
python api_server.py
```

サーバーは `http://localhost:5000` で起動します。

### 4. フロントエンドの起動

React開発環境がある場合：

```bash
# 新規Reactプロジェクトを作成
npx create-react-app safety-law-tracker
cd safety-law-tracker

# safety-law-tracker-enhanced.jsxを src/App.js にコピー
cp ../safety-law-tracker-enhanced.jsx src/App.js

# 依存パッケージをインストール
npm install lucide-react

# 開発サーバー起動
npm start
```

## 使い方

### Web UI

1. ブラウザで `http://localhost:3000` にアクセス
2. 検索ボックスで法令名や内容を検索
3. ステージフィルターで進捗状況を絞り込み
4. 各改正項目をクリックして詳細を表示
5. PDF資料や公式ページへのリンクにアクセス

### API エンドポイント

#### 改正情報一覧の取得
```bash
GET /api/revisions
# パラメータ:
#   - stage: 'all' | 'public_comment' | 'deliberation' | 'promulgated' | 'enforcement_scheduled' | 'enforced'
#   - search: 検索キーワード

# 例
curl http://localhost:5000/api/revisions?stage=promulgated
```

#### 特定改正情報の詳細
```bash
GET /api/revision/<revision_id>

# 例
curl http://localhost:5000/api/revision/mhlw_main_1
```

#### 統計情報の取得
```bash
GET /api/stats
```

#### データの手動更新
```bash
POST /api/refresh
```

### スクリプトの直接実行

データ収集スクリプトを単独で実行：

```bash
python scraper.py
```

実行後、以下のファイルが生成されます：
- `law_revisions_data.json` - 収集した生データ
- `revisions_list.json` - 整形済み改正情報リスト

## 自動更新スケジュール

APIサーバーは以下のスケジュールで自動的にデータを更新します：

- **毎日 午前8時** - 全情報源から最新データを収集

手動更新も可能です：
```bash
curl -X POST http://localhost:5000/api/refresh
```

## データ形式

### 改正情報オブジェクト

```json
{
  "id": "mhlw_main_1",
  "lawId": "roudouanzeneisei",
  "lawName": "労働安全衛生法及び作業環境測定法",
  "title": "労働安全衛生法及び作業環境測定法の一部を改正する法律",
  "stage": "promulgated",
  "publicationDate": "2025-05-14",
  "promulgationDate": "2025-05-14",
  "enforcementDate": "2026-04-01",
  "description": "改正の概要...",
  "officialUrl": "https://www.mhlw.go.jp/...",
  "pdfUrls": [
    {
      "name": "概要",
      "url": "https://www.mhlw.go.jp/.../001497667.pdf"
    }
  ],
  "highlights": [
    "フリーランスへの安全衛生対策",
    "50人未満事業場でのストレスチェック義務化"
  ]
}
```

## 実装済み機能

✅ 厚生労働省公式ページのスクレイピング
✅ PDF資料リンクの自動収集
✅ 改正プロセスの可視化
✅ 検索・フィルター機能
✅ 施行日カウントダウン
✅ REST API
✅ 自動更新スケジューラー

## 今後の拡張予定

🔲 e-Gov パブリックコメントAPI連携
🔲 e-Gov 法令検索API連携
🔲 官報情報の自動取得
🔲 メール通知機能
🔲 RSS/Atomフィード配信
🔲 データベース保存（SQLite/PostgreSQL）
🔲 変更履歴の追跡
🔲 差分表示機能

## 注意事項

1. **スクレイピングについて**
   - サーバーに負荷をかけないよう、リクエスト間隔を空けています
   - robots.txtを遵守してください
   - 商用利用の場合は各サイトの利用規約を確認してください

2. **データの正確性**
   - 自動収集したデータは参考情報です
   - 重要な情報は必ず公式サイトで確認してください

3. **API制限**
   - 一部のAPIは認証が必要です
   - APIキーが必要な場合は適切に管理してください

## ライセンス

MIT License

## 作成者

Hayato

## 更新履歴

- 2026-02-03: 初版リリース
  - フロントエンド実装
  - データ収集スクリプト
  - APIサーバー
  - 自動更新機能

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。

## 貢献

Pull Requestを歓迎します！

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
