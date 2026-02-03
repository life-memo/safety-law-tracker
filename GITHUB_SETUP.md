# GitHub公開手順

このドキュメントでは、労働安全衛生法令改正追跡システムをGitHubに公開する手順を説明します。

## 📋 前提条件

- GitHubアカウントを持っていること
- Gitがインストールされていること
- ターミナル（コマンドライン）の基本操作ができること

## 🚀 公開手順

### 1. GitHubで新しいリポジトリを作成

1. [GitHub](https://github.com)にログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ情報を入力:
   - **Repository name**: `safety-law-tracker`
   - **Description**: `労働安全衛生法令改正追跡システム`
   - **Public** or **Private**: お好みで選択
   - **Initialize this repository**: チェックを入れない（重要！）
4. 「Create repository」をクリック

### 2. ローカルリポジトリの初期化

ダウンロードしたファイルがあるディレクトリで以下のコマンドを実行:

```bash
# Gitリポジトリを初期化
git init

# すべてのファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit: 労働安全衛生法令改正追跡システム"

# メインブランチの名前を確認（mainまたはmaster）
git branch -M main
```

### 3. GitHubリポジトリと接続

GitHubで作成したリポジトリのURLを使用:

```bash
# リモートリポジトリを追加（YOUR_USERNAMEを自分のユーザー名に置き換える）
git remote add origin https://github.com/YOUR_USERNAME/safety-law-tracker.git

# プッシュ
git push -u origin main
```

### 4. README.mdの編集

GitHub上で以下の項目を編集:

1. `YOUR_USERNAME`を実際のGitHubユーザー名に置き換え
2. スクリーンショットを追加する場合は、`docs/`フォルダを作成して画像をアップロード

### 5. リポジトリ設定（オプション）

#### About（説明）を設定

リポジトリページの右上「About」の⚙️アイコンをクリック:
- **Description**: 労働安全衛生法令改正追跡システム
- **Website**: デモサイトのURLがあれば追加
- **Topics**: `labor-law`, `japan`, `safety`, `health`, `web-scraping`, `react`, `python`, `flask`

#### GitHub Pages（オプション）

静的サイトをホスティングする場合:
1. Settings → Pages
2. Source: `main` ブランチを選択
3. フォルダ: `/root` または `/docs`
4. Save

## 📝 公開後のチェックリスト

- [ ] README.mdが正しく表示されているか
- [ ] LICENSEファイルが含まれているか
- [ ] .gitignoreが機能しているか（`node_modules/`や`.env`が除外されているか）
- [ ] すべての機密情報が除外されているか

## 🔒 セキュリティチェック

公開前に以下を確認:

- [ ] APIキーや認証情報が含まれていないか
- [ ] 個人情報が含まれていないか
- [ ] 内部URLやIPアドレスが含まれていないか

## 📢 公開の告知

### Twitter/SNS投稿例

```
🚀 労働安全衛生法令改正追跡システムをGitHubで公開しました！

厚生労働省などから法令改正情報を自動収集し、
改正プロセスごとに整理して表示します。

👉 https://github.com/YOUR_USERNAME/safety-law-tracker

#労働安全衛生法 #法令改正 #OSS #Python #React
```

### Qiita記事（オプション）

以下のような記事を書くと、より多くの人に知ってもらえます:

- 「労働安全衛生法令の改正情報を自動追跡するシステムを作った」
- 「PythonとReactで作る法令改正トラッカー」
- 「Web ScrapingとAPIサーバーの実装Tips」

## 🤝 コントリビューションの受け入れ

CONTRIBUTING.mdを参照するよう、READMEに記載済みです。

Issues や Pull Requests を積極的に受け入れましょう！

## 🎉 おめでとうございます！

これでGitHubでの公開は完了です。

コミュニティからのフィードバックを活かして、
より良いシステムに育てていきましょう！

---

## トラブルシューティング

### Pushがrejectされる

```bash
git pull origin main --rebase
git push origin main
```

### リモートURLを間違えた

```bash
git remote set-url origin https://github.com/YOUR_USERNAME/safety-law-tracker.git
```

### 大きなファイルがある

```bash
# 100MB以上のファイルは削除するか、Git LFSを使用
git filter-branch --tree-filter 'rm -rf path/to/large/file' HEAD
```

---

質問や問題があれば、GitHubのIssuesで相談してください！
