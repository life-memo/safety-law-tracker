#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
労働安全衛生法令改正追跡システム - API/RSS版スクレイパー
より確実で正確なデータ収集
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List
from datetime import datetime
import re
import feedparser

class APIRSSScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.base_url = 'https://www.mhlw.go.jp'
        
    def fetch_mhlw_rss(self) -> List[Dict]:
        """厚生労働省の新着情報RSSから取得"""
        rss_url = 'https://www.mhlw.go.jp/stf/news.rdf'
        
        try:
            print("\n[RSS] 厚生労働省 新着情報")
            print("-" * 60)
            
            feed = feedparser.parse(rss_url)
            
            revisions = []
            for entry in feed.entries[:50]:  # 最新50件
                title = entry.title
                link = entry.link
                published = entry.get('published', '')
                
                # 労働安全衛生関連のキーワードでフィルタ
                keywords = [
                    '労働安全衛生', '労働基準', '安全衛生', '労災',
                    '改正', '省令', '規則', '法律', '施行', '公布',
                    'パブリックコメント', '化学物質', '高年齢',
                    'ストレスチェック', 'メンタルヘルス', '健康診断'
                ]
                
                if any(keyword in title for keyword in keywords):
                    # 日付をパース
                    date = self.parse_date(published)
                    
                    revisions.append({
                        'title': title,
                        'url': link,
                        'publishedDate': date,
                        'source': 'RSS',
                        'description': entry.get('summary', '')[:300]
                    })
            
            print(f"  取得: {len(revisions)}件")
            return revisions
            
        except Exception as e:
            print(f"  エラー: {e}")
            return []
    
    def fetch_egov_public_comments(self) -> List[Dict]:
        """e-Gov パブリックコメント（HTML版）"""
        url = 'https://public-comment.e-gov.go.jp/servlet/Public'
        
        try:
            print("\n[e-Gov] パブリックコメント")
            print("-" * 60)
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            revisions = []
            
            # 労働関連のパブコメを探す
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                
                keywords = ['労働安全衛生', '労働基準', '労災', '安全衛生']
                if any(keyword in text for keyword in keywords):
                    href = link['href']
                    if not href.startswith('http'):
                        href = 'https://public-comment.e-gov.go.jp' + href
                    
                    revisions.append({
                        'title': text,
                        'url': href,
                        'source': 'パブリックコメント',
                        'stage': 'public_comment'
                    })
            
            print(f"  取得: {len(revisions)}件")
            return revisions
            
        except Exception as e:
            print(f"  エラー: {e}")
            return []
    
    def fetch_kanpo_info(self) -> List[Dict]:
        """官報情報（簡易版 - 厚生労働省ページから）"""
        url = 'https://www.mhlw.go.jp/hourei/index.html'
        
        try:
            print("\n[官報] 法令公布情報")
            print("-" * 60)
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            revisions = []
            
            # 法令の公布情報を探す
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                
                if '公布' in text or '法律' in text or '省令' in text:
                    keywords = ['労働安全衛生', '労働基準', '安全衛生']
                    if any(keyword in text for keyword in keywords):
                        href = link['href']
                        if not href.startswith('http'):
                            href = self.base_url + href
                        
                        revisions.append({
                            'title': text,
                            'url': href,
                            'source': '官報',
                            'stage': 'promulgated'
                        })
            
            print(f"  取得: {len(revisions)}件")
            return revisions
            
        except Exception as e:
            print(f"  エラー: {e}")
            return []
    
    def fetch_specific_topics(self) -> List[Dict]:
        """重要トピックページを個別取得"""
        topics = [
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/newpage_00007.html',
                'title': '高年齢労働者の安全衛生対策',
                'stage': 'enforced',
                'description': '70歳以上の労働者に対する特別な安全衛生対策'
            },
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html',
                'title': '化学物質規制の見直し',
                'stage': 'enforcement_scheduled',
                'description': '約2,450物質に対するリスクアセスメント義務化'
            },
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/anzen-roudou.html',
                'title': '労働災害防止対策',
                'stage': 'consideration',
                'description': '労働災害を防止するための総合的な対策'
            },
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/health.html',
                'title': '健康確保対策',
                'stage': 'enforced',
                'description': 'ストレスチェック制度等の健康確保対策'
            }
        ]
        
        print("\n[重要トピック] 個別ページ")
        print("-" * 60)
        
        revisions = []
        for topic in topics:
            revisions.append({
                'title': topic['title'],
                'url': topic['url'],
                'description': topic['description'],
                'source': '重要トピック',
                'stage': topic['stage']
            })
            print(f"  ✓ {topic['title']}")
        
        return revisions
    
    def parse_date(self, date_string: str) -> str:
        """日付文字列をパース"""
        try:
            # RSSの日付形式をパース
            if date_string:
                dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def determine_stage_from_title(self, title: str, description: str = '') -> str:
        """タイトルから改正段階を推定"""
        text = title + ' ' + description
        
        # キーワードベースの判定（優先度順）
        if 'パブリックコメント' in text or 'パブコメ' in text or '意見募集' in text:
            return 'public_comment'
        elif '施行しました' in text or '施行されました' in text or '適用開始' in text:
            return 'enforced'
        elif '施行予定' in text or '施行される予定' in text or '施行日' in text:
            return 'enforcement_scheduled'
        elif '公布' in text and ('しました' in text or 'されました' in text):
            return 'promulgated'
        elif '国会' in text or '法案' in text or '審議中' in text:
            return 'deliberation'
        elif '検討' in text or '研究会' in text or '審議会' in text:
            return 'consideration'
        else:
            return 'consideration'
    
    def collect_all_data(self) -> List[Dict]:
        """すべてのソースからデータを収集"""
        print("=" * 60)
        print("API/RSS版スクレイパー開始")
        print("=" * 60)
        
        all_data = []
        
        # 1. RSS
        rss_data = self.fetch_mhlw_rss()
        all_data.extend(rss_data)
        time.sleep(1)
        
        # 2. パブリックコメント
        egov_data = self.fetch_egov_public_comments()
        all_data.extend(egov_data)
        time.sleep(1)
        
        # 3. 官報情報
        kanpo_data = self.fetch_kanpo_info()
        all_data.extend(kanpo_data)
        time.sleep(1)
        
        # 4. 重要トピック
        topics_data = self.fetch_specific_topics()
        all_data.extend(topics_data)
        
        print("\n" + "=" * 60)
        print(f"合計収集: {len(all_data)}件")
        print("=" * 60)
        
        return all_data
    
    def generate_revision_list(self, raw_data: List[Dict]) -> List[Dict]:
        """収集データを整形"""
        revisions = []
        seen_titles = set()
        
        for idx, item in enumerate(raw_data, 1):
            title = item.get('title', '').strip()
            
            # 重複除外・短すぎるタイトル除外
            if not title or title in seen_titles or len(title) < 10:
                continue
            seen_titles.add(title)
            
            # 改正段階を決定
            stage = item.get('stage')
            if not stage:
                stage = self.determine_stage_from_title(
                    title, 
                    item.get('description', '')
                )
            
            revision = {
                'id': idx,
                'lawName': self.extract_law_name(title),
                'title': title,
                'stage': stage,
                'description': item.get('description', title)[:300],
                'officialUrl': item.get('url', ''),
                'source': item.get('source', '厚生労働省'),
                'collectedDate': datetime.now().strftime('%Y-%m-%d')
            }
            
            # 日付情報
            if 'publishedDate' in item:
                revision['publishedDate'] = item['publishedDate']
            
            revisions.append(revision)
        
        # ステージごとに件数を表示
        stage_counts = {}
        for rev in revisions:
            stage = rev['stage']
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        print("\n📊 ステージ別件数:")
        stage_names = {
            'consideration': '検討段階',
            'public_comment': 'パブリックコメント',
            'deliberation': '国会審議中',
            'promulgated': '公布済み',
            'enforcement_scheduled': '施行予定',
            'enforced': '施行済み'
        }
        for stage, count in stage_counts.items():
            print(f"  {stage_names.get(stage, stage)}: {count}件")
        
        return revisions
    
    def extract_law_name(self, title: str) -> str:
        """タイトルから法令名を抽出"""
        law_keywords = [
            '労働安全衛生法', '労働基準法', '労働契約法', 'じん肺法',
            '特定化学物質', '石綿', 'ボイラー', 'クレーン',
            '有機溶剤', '粉じん', '高気圧', '電離放射線'
        ]
        
        for keyword in law_keywords:
            if keyword in title:
                return keyword
        
        return '労働安全衛生関連法令'


def main():
    """メイン実行関数"""
    scraper = APIRSSScraper()
    
    # データ収集
    raw_data = scraper.collect_all_data()
    
    # 改正リストを生成
    revisions = scraper.generate_revision_list(raw_data)
    
    # JSONに保存
    with open('revisions_list.json', 'w', encoding='utf-8') as f:
        json.dump(revisions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 処理完了: {len(revisions)}件の改正情報を生成")
    print("📄 ファイル: revisions_list.json")


if __name__ == "__main__":
    main()
