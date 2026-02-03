#!/bin/bash

# 労働安全衛生法令改正追跡システム セットアップスクリプト

echo "=========================================="
echo "労働安全衛生法令改正追跡システム"
echo "セットアップを開始します"
echo "=========================================="
echo ""

# Pythonバージョンチェック
echo "Pythonバージョンを確認しています..."
python3 --version
if [ $? -ne 0 ]; then
    echo "エラー: Python 3がインストールされていません"
    exit 1
fi

# Node.jsバージョンチェック
echo "Node.jsバージョンを確認しています..."
node --version
if [ $? -ne 0 ]; then
    echo "警告: Node.jsがインストールされていません（フロントエンド開発に必要）"
fi

echo ""
echo "=========================================="
echo "バックエンドのセットアップ"
echo "=========================================="

# Python依存パッケージのインストール
echo "Python依存パッケージをインストールしています..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "エラー: パッケージのインストールに失敗しました"
    exit 1
fi

echo ""
echo "✅ バックエンドのセットアップ完了"
echo ""

# Node.jsがインストールされている場合のみフロントエンドセットアップ
if command -v node &> /dev/null; then
    echo "=========================================="
    echo "フロントエンドのセットアップ"
    echo "=========================================="
    
    # Reactプロジェクトの作成
    if [ ! -d "frontend" ]; then
        echo "Reactプロジェクトを作成しています..."
        npx create-react-app frontend
        
        cd frontend
        
        # 依存パッケージのインストール
        echo "依存パッケージをインストールしています..."
        npm install lucide-react
        npm install -D tailwindcss postcss autoprefixer
        
        # Tailwind設定
        npx tailwindcss init -p
        
        # コンポーネントファイルをコピー
        cp ../safety-law-tracker-fixed.jsx src/App.js
        
        cd ..
        
        echo ""
        echo "✅ フロントエンドのセットアップ完了"
    else
        echo "frontendディレクトリが既に存在します。スキップします。"
    fi
fi

echo ""
echo "=========================================="
echo "セットアップ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo ""
echo "1. バックエンドを起動:"
echo "   python3 api_server.py"
echo ""
echo "2. フロントエンドを起動（別のターミナルで）:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. ブラウザで以下にアクセス:"
echo "   http://localhost:3000"
echo ""
echo "=========================================="
