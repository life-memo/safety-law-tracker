# 🚀 5分でできる！セットアップ手順

## ステップ1: GitHubにアップロード

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/safety-law-tracker.git
git push -u origin main
```

## ステップ2: GitHub Actions 権限

1. GitHubリポジトリ → **Settings**
2. **Actions** → **General**
3. **Workflow permissions**
4. ✅ **Read and write permissions**
5. **Save**

## ステップ3: 初回実行

1. **Actions** タブ
2. **Update Law Data**
3. **Run workflow**
4. 緑のチェック ✅ が出たら成功！

## ステップ4: Cloudflare Pages

1. [dash.cloudflare.com](https://dash.cloudflare.com)
2. **Workers & Pages** → **Create**
3. **Connect to Git** → リポジトリ選択
4. **Framework**: Create React App
5. **Build command**: `npm run build`
6. **Build output**: `build`
7. **Deploy**

## 完成！ 🎉

URL: `https://safety-law-tracker.pages.dev`

毎日午前8時に自動更新されます！
