"""
労働安全衛生法令改正情報 API サーバー

機能:
- 改正情報の提供 (REST API)
- 定期的な情報更新 (スケジューラー)
- キャッシング
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json
import os
from scraper import SafetyLawScraper

app = Flask(__name__)
CORS(app)  # フロントエンドからのアクセスを許可

# データキャッシュ
cached_data = {
    'revisions': [],
    'last_updated': None,
    'next_update': None
}

# データファイルのパス
DATA_FILE = 'law_revisions_data.json'
REVISIONS_FILE = 'revisions_list.json'


def load_cached_data():
    """キャッシュされたデータを読み込む"""
    global cached_data
    
    if os.path.exists(REVISIONS_FILE):
        with open(REVISIONS_FILE, 'r', encoding='utf-8') as f:
            cached_data['revisions'] = json.load(f)
        
        # ファイルの更新時刻を取得
        mtime = os.path.getmtime(REVISIONS_FILE)
        cached_data['last_updated'] = datetime.fromtimestamp(mtime).isoformat()
    
    print(f"キャッシュデータ読み込み完了: {len(cached_data['revisions'])}件")


def update_data():
    """データを更新（スケジューラーから呼ばれる）"""
    print(f"\n[{datetime.now()}] データ更新開始...")
    
    try:
        scraper = SafetyLawScraper()
        
        # データ収集
        data = scraper.collect_all_data()
        scraper.save_to_json(data, DATA_FILE)
        
        # 改正リストを生成
        revisions = scraper.generate_revision_list(data)
        
        with open(REVISIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(revisions, f, ensure_ascii=False, indent=2)
        
        # キャッシュを更新
        load_cached_data()
        
        print(f"[{datetime.now()}] データ更新完了: {len(revisions)}件")
        
    except Exception as e:
        print(f"[{datetime.now()}] データ更新エラー: {e}")


@app.route('/api/revisions', methods=['GET'])
def get_revisions():
    """改正情報一覧を取得"""
    stage = request.args.get('stage', 'all')
    search = request.args.get('search', '')
    
    revisions = cached_data['revisions']
    
    # フィルタリング
    if stage != 'all':
        revisions = [r for r in revisions if r.get('stage') == stage]
    
    if search:
        revisions = [
            r for r in revisions 
            if search.lower() in r.get('title', '').lower() 
            or search.lower() in r.get('description', '').lower()
            or search.lower() in r.get('lawName', '').lower()
        ]
    
    return jsonify({
        'success': True,
        'data': revisions,
        'count': len(revisions),
        'last_updated': cached_data['last_updated'],
        'next_update': cached_data['next_update']
    })


@app.route('/api/revision/<revision_id>', methods=['GET'])
def get_revision_detail(revision_id):
    """特定の改正情報の詳細を取得"""
    revision = next(
        (r for r in cached_data['revisions'] if r.get('id') == revision_id),
        None
    )
    
    if revision:
        return jsonify({
            'success': True,
            'data': revision
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Revision not found'
        }), 404


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """統計情報を取得"""
    revisions = cached_data['revisions']
    
    # ステージ別の件数
    stage_counts = {}
    for revision in revisions:
        stage = revision.get('stage', 'unknown')
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    # 直近の更新
    recent_updates = sorted(
        [r for r in revisions if r.get('promulgationDate')],
        key=lambda x: x.get('promulgationDate', ''),
        reverse=True
    )[:5]
    
    return jsonify({
        'success': True,
        'data': {
            'total_count': len(revisions),
            'stage_counts': stage_counts,
            'recent_updates': recent_updates,
            'last_updated': cached_data['last_updated']
        }
    })


@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    """手動でデータを更新"""
    try:
        update_data()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'last_updated': cached_data['last_updated']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_loaded': len(cached_data['revisions']) > 0
    })


@app.route('/', methods=['GET'])
def index():
    """APIルートの説明"""
    return jsonify({
        'name': '労働安全衛生法令改正情報 API',
        'version': '1.0.0',
        'endpoints': {
            '/api/revisions': 'GET - 改正情報一覧の取得',
            '/api/revision/<id>': 'GET - 特定改正情報の詳細',
            '/api/stats': 'GET - 統計情報',
            '/api/refresh': 'POST - データの手動更新',
            '/api/health': 'GET - ヘルスチェック'
        },
        'data_sources': [
            '厚生労働省 労働安全衛生法改正ページ',
            '厚生労働省 化学物質規制ページ',
            '安全衛生情報センター',
            'e-Gov パブリックコメント'
        ]
    })


def init_scheduler():
    """スケジューラーを初期化"""
    scheduler = BackgroundScheduler()
    
    # 毎日午前8時にデータを更新
    scheduler.add_job(
        func=update_data,
        trigger='cron',
        hour=8,
        minute=0,
        id='daily_update'
    )
    
    # 次回更新時刻を設定
    next_run = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    if next_run < datetime.now():
        next_run += timedelta(days=1)
    cached_data['next_update'] = next_run.isoformat()
    
    scheduler.start()
    print(f"スケジューラー起動: 次回更新 {next_run}")


if __name__ == '__main__':
    print("=" * 60)
    print("労働安全衛生法令改正情報 APIサーバー")
    print("=" * 60)
    
    # 初期データ読み込み
    load_cached_data()
    
    # データがない場合は初回更新
    if len(cached_data['revisions']) == 0:
        print("\n初回データ取得中...")
        update_data()
    
    # スケジューラー起動
    init_scheduler()
    
    # サーバー起動
    print("\nAPIサーバー起動中...")
    print("アクセス: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
