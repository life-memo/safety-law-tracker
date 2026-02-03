# 労働安全衛生法令改正追跡システム

労働安全衛生関連法令の改正情報を自動収集・追跡するWebアプリケーション

## 🚀 クイックスタート

### 1. GitHubにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/safety-law-tracker.git
git push -u origin main
```

### 2. GitHub Actions 権限設定

1. Settings → Actions → General
2. Workflow permissions で「Read and write permissions」を選択

### 3. GitHub Actions 実行

1. Actions タブ → Update Law Data
2. Run workflow

### 4. Cloudflare Pages デプロイ

1. [dash.cloudflare.com](https://dash.cloudflare.com)
2. Workers & Pages → Create → Connect to Git
3. Framework: Create React App
4. Build command: `npm run build`
5. Build output: `build`

## ✨ 特徴

- 毎日午前8時に自動更新
- 完全無料・サーバー不要
- 6段階のプロセス可視化

## 📝 ライセンス

MIT License
