"""
労働安全衛生法令改正情報 自動収集スクリプト

このスクリプトは以下のソースから最新の改正情報を収集します：
1. 厚生労働省の公式ページ
2. e-Gov パブリックコメント
3. 安全衛生情報センター
4. e-Gov 法令検索
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from typing import List, Dict
import time

class SafetyLawScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.revisions = []
        
    def scrape_mhlw_main_page(self):
        """厚生労働省の労働安全衛生法改正ページをスクレイピング"""
        url = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/an-eihou/index_00001.html"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトルと概要を取得
            title = soup.find('h1')
            if title:
                print(f"ページタイトル: {title.text.strip()}")
            
            # PDFリンクを収集
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    link_text = link.text.strip()
                    if not href.startswith('http'):
                        href = 'https://www.mhlw.go.jp' + href
                    pdf_links.append({
                        'name': link_text,
                        'url': href
                    })
            
            print(f"PDF資料数: {len(pdf_links)}")
            return {
                'title': title.text.strip() if title else '',
                'url': url,
                'pdf_links': pdf_links,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error scraping MHLW page: {e}")
            return None
    
    def scrape_mhlw_chemical_page(self):
        """化学物質規制に関するページをスクレイピング"""
        url = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('h1')
            if title:
                print(f"化学物質ページタイトル: {title.text.strip()}")
            
            # 改正情報を探す
            revisions = []
            for heading in soup.find_all(['h2', 'h3']):
                heading_text = heading.text.strip()
                if '改正' in heading_text or '省令' in heading_text or '政令' in heading_text:
                    # 日付を抽出
                    date_match = re.search(r'令和(\d+)年(\d+)月(\d+)日', heading_text)
                    if date_match:
                        year = int(date_match.group(1)) + 2018  # 令和→西暦変換
                        month = int(date_match.group(2))
                        day = int(date_match.group(3))
                        
                        revisions.append({
                            'title': heading_text,
                            'date': f"{year}-{month:02d}-{day:02d}",
                            'url': url
                        })
            
            print(f"化学物質関連改正数: {len(revisions)}")
            return revisions
            
        except Exception as e:
            print(f"Error scraping chemical page: {e}")
            return []
    
    def scrape_egov_public_comments(self):
        """e-Govのパブリックコメントを検索"""
        # 注: 実際のe-Gov APIは認証が必要な場合があります
        url = "https://public-comment.e-gov.go.jp/servlet/Public"
        
        # キーワード検索
        keywords = ['労働安全衛生法', '労働安全衛生規則', '化学物質', '作業環境測定法']
        
        print("e-Govパブリックコメント検索（実際のAPIキーが必要）")
        # 実際の実装では、APIキーを使用して検索を実行
        
        return []
    
    def scrape_jaish_updates(self):
        """安全衛生情報センターの新着情報を取得"""
        url = "https://www.jaish.gr.jp/user/anzen/hor/horei_index.html"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("安全衛生情報センター - 法令更新情報")
            
            # 新着情報を抽出
            updates = []
            for item in soup.find_all('span', class_='index-1'):
                text = item.text.strip()
                if '令和' in text and ('改正' in text or '公布' in text):
                    updates.append(text)
                    print(f"  - {text}")
            
            return updates
            
        except Exception as e:
            print(f"Error scraping JAISH: {e}")
            return []
    
    def extract_date_from_text(self, text: str) -> str:
        """テキストから日付を抽出"""
        # 令和表記の日付を抽出
        match = re.search(r'令和(\d+)年(\d+)月(\d+)日', text)
        if match:
            year = int(match.group(1)) + 2018
            month = int(match.group(2))
            day = int(match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        # 西暦表記の日付を抽出
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        return None
    
    def collect_all_data(self) -> Dict:
        """すべての情報源から データを収集"""
        print("=" * 60)
        print("労働安全衛生法令改正情報 自動収集開始")
        print("=" * 60)
        
        data = {
            'collected_at': datetime.now().isoformat(),
            'sources': {}
        }
        
        # 1. 厚生労働省メインページ
        print("\n[1] 厚生労働省 - 労働安全衛生法改正ページ")
        print("-" * 60)
        mhlw_main = self.scrape_mhlw_main_page()
        if mhlw_main:
            data['sources']['mhlw_main'] = mhlw_main
        time.sleep(1)  # サーバーに負荷をかけないよう待機
        
        # 2. 化学物質規制ページ
        print("\n[2] 厚生労働省 - 化学物質規制ページ")
        print("-" * 60)
        chemical_revisions = self.scrape_mhlw_chemical_page()
        data['sources']['mhlw_chemical'] = chemical_revisions
        time.sleep(1)
        
        # 3. 安全衛生情報センター
        print("\n[3] 安全衛生情報センター")
        print("-" * 60)
        jaish_updates = self.scrape_jaish_updates()
        data['sources']['jaish'] = jaish_updates
        time.sleep(1)
        
        # 4. e-Govパブリックコメント（要実装）
        print("\n[4] e-Gov パブリックコメント")
        print("-" * 60)
        egov_comments = self.scrape_egov_public_comments()
        data['sources']['egov_public_comments'] = egov_comments
        
        print("\n" + "=" * 60)
        print("収集完了")
        print("=" * 60)
        
        return data
    
    def save_to_json(self, data: Dict, filename: str = 'law_revisions_data.json'):
        """収集したデータをJSONファイルに保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nデータを {filename} に保存しました")
    
    def generate_revision_list(self, data: Dict) -> List[Dict]:
        """収集データから改正情報リストを生成"""
        revisions = []
        
        # MHLWメインページのデータを処理
        if 'mhlw_main' in data['sources']:
            main = data['sources']['mhlw_main']
            if main:
                revision = {
                    'id': 'mhlw_main_1',
                    'lawName': '労働安全衛生法及び作業環境測定法',
                    'title': main.get('title', ''),
                    'stage': 'promulgated',
                    'promulgationDate': '2025-05-14',
                    'officialUrl': main.get('url', ''),
                    'pdfUrls': main.get('pdf_links', []),
                    'description': '多様な人材が安全に働き続けられる職場環境の整備を推進'
                }
                revisions.append(revision)
        
        # 化学物質関連の改正を追加
        if 'mhlw_chemical' in data['sources']:
            for idx, chem in enumerate(data['sources']['mhlw_chemical']):
                revision = {
                    'id': f'chemical_{idx}',
                    'lawName': '特定化学物質障害予防規則等',
                    'title': chem.get('title', ''),
                    'stage': 'enforcement_scheduled',
                    'promulgationDate': chem.get('date', ''),
                    'officialUrl': chem.get('url', ''),
                    'description': '化学物質管理の強化'
                }
                revisions.append(revision)
        
        return revisions


def main():
    """メイン実行関数"""
    scraper = SafetyLawScraper()
    
    # データ収集
    data = scraper.collect_all_data()
    
    # JSONに保存
    scraper.save_to_json(data)
    
    # 改正リストを生成
    revisions = scraper.generate_revision_list(data)
    
    print(f"\n生成された改正情報: {len(revisions)}件")
    
    # 改正リストも保存
    with open('revisions_list.json', 'w', encoding='utf-8') as f:
        json.dump(revisions, f, ensure_ascii=False, indent=2)
    
    print("\n処理が完了しました！")
    print("生成されたファイル:")
    print("  - law_revisions_data.json: 収集した生データ")
    print("  - revisions_list.json: 整形済み改正情報リスト")


if __name__ == "__main__":
    main()
