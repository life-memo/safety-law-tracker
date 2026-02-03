#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
労働安全衛生法令改正追跡システム - 改良版スクレイパー
複数のページから自動的に改正情報を収集
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List
from datetime import datetime
import re

class EnhancedSafetyLawScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.base_url = 'https://www.mhlw.go.jp'
        
    def scrape_main_pages(self) -> List[Dict]:
        """複数の主要ページから情報を収集"""
        pages = [
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html',
                'name': 'メインページ'
            },
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/an-eihou/index_00001.html',
                'name': '改正法ページ'
            },
            {
                'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html',
                'name': '化学物質規制ページ'
            }
        ]
        
        all_links = []
        
        for page in pages:
            print(f"\n[{page['name']}] {page['url']}")
            links = self.extract_links_from_page(page['url'])
            all_links.extend(links)
            time.sleep(1)
        
        return all_links
    
    def extract_links_from_page(self, url: str) -> List[Dict]:
        """ページから関連リンクを抽出"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            
            # すべてのリンクを取得
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # 改正・対策・規則に関連するキーワード
                keywords = [
                    '改正', '対策', '規則', '省令', '施行', '公布',
                    '高年齢', '化学物質', '熱中症', 'ストレスチェック',
                    'リスクアセスメント', '安全衛生', 'パブリックコメント'
                ]
                
                # キーワードに該当するリンクのみ収集
                if any(keyword in text for keyword in keywords):
                    # 相対URLを絶対URLに変換
                    if href.startswith('/'):
                        href = self.base_url + href
                    elif not href.startswith('http'):
                        continue
                    
                    # PDFや外部リンクは除外
                    if '.pdf' in href.lower() or 'e-gov.go.jp' in href:
                        continue
                    
                    links.append({
                        'title': text,
                        'url': href
                    })
            
            print(f"  → {len(links)}件のリンクを発見")
            return links
            
        except Exception as e:
            print(f"  エラー: {e}")
            return []
    
    def analyze_page_content(self, url: str, title: str) -> Dict:
        """個別ページの内容を解析"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ページの主要な情報を抽出
            description = ""
            
            # 最初の段落を取得
            paragraphs = soup.find_all('p')
            if paragraphs:
                description = ' '.join([p.get_text(strip=True) for p in paragraphs[:2]])
                description = description[:300]  # 最大300文字
            
            # 日付を探す
            dates = self.extract_dates(soup.get_text())
            
            # PDFリンクを収集
            pdf_links = []
            for link in soup.find_all('a', href=True):
                if '.pdf' in link['href'].lower():
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = self.base_url + pdf_url
                    pdf_links.append({
                        'name': link.get_text(strip=True),
                        'url': pdf_url
                    })
            
            return {
                'title': title,
                'url': url,
                'description': description,
                'dates': dates,
                'pdfUrls': pdf_links[:5]  # 最大5件
            }
            
        except Exception as e:
            print(f"  ページ解析エラー: {e}")
            return None
    
    def extract_dates(self, text: str) -> Dict:
        """テキストから日付を抽出"""
        dates = {}
        
        # 令和年度パターン
        reiwa_pattern = r'令和(\d+)年(\d+)月(\d+)日'
        matches = re.findall(reiwa_pattern, text)
        if matches:
            # 最初の日付を使用（通常は公布日や施行日）
            r_year, month, day = matches[0]
            year = 2018 + int(r_year)  # 令和元年=2019年
            dates['date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 西暦パターン
        year_pattern = r'20(\d{2})年(\d{1,2})月(\d{1,2})日'
        matches = re.findall(year_pattern, text)
        if matches and 'date' not in dates:
            year, month, day = matches[0]
            dates['date'] = f"20{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return dates
    
    def determine_stage(self, title: str, description: str) -> str:
        """タイトルと説明から改正段階を判定"""
        text = (title + ' ' + description).lower()
        
        if 'パブリックコメント' in text or 'パブコメ' in text or '意見募集' in text:
            return 'public_comment'
        elif '施行' in text and ('済' in text or '開始' in text):
            return 'enforced'
        elif '施行予定' in text or '施行日' in text:
            return 'enforcement_scheduled'
        elif '公布' in text:
            return 'promulgated'
        elif '国会' in text or '審議' in text:
            return 'deliberation'
        else:
            return 'consideration'
    
    def collect_all_data(self) -> List[Dict]:
        """すべてのデータを収集"""
        print("=" * 60)
        print("改良版スクレイパー開始")
        print("=" * 60)
        
        # 主要ページからリンクを収集
        all_links = self.scrape_main_pages()
        
        # 重複を削除
        unique_links = {link['url']: link for link in all_links}.values()
        print(f"\n重複を除外: {len(unique_links)}件のユニークなページ")
        
        # 各ページの詳細を取得
        revisions = []
        for i, link in enumerate(list(unique_links)[:20], 1):  # 最大20ページ
            print(f"\n[{i}] {link['title'][:50]}...")
            
            content = self.analyze_page_content(link['url'], link['title'])
            if content:
                stage = self.determine_stage(content['title'], content['description'])
                
                revision = {
                    'id': i,
                    'lawName': self.extract_law_name(content['title']),
                    'title': content['title'],
                    'stage': stage,
                    'description': content['description'],
                    'officialUrl': content['url'],
                    'pdfUrls': content['pdfUrls']
                }
                
                # 日付情報があれば追加
                if content['dates'].get('date'):
                    if stage in ['enforced', 'enforcement_scheduled']:
                        revision['enforcementDate'] = content['dates']['date']
                    else:
                        revision['promulgationDate'] = content['dates']['date']
                
                revisions.append(revision)
                print(f"  ✓ 追加: {stage}")
            
            time.sleep(0.5)  # サーバーに負荷をかけない
        
        print(f"\n合計 {len(revisions)} 件の改正情報を収集")
        return revisions
    
    def extract_law_name(self, title: str) -> str:
        """タイトルから法令名を抽出"""
        law_keywords = [
            '労働安全衛生法', '労働基準法', '労働契約法', 'じん肺法',
            '特定化学物質', '石綿', 'ボイラー', 'クレーン'
        ]
        
        for keyword in law_keywords:
            if keyword in title:
                return keyword
        
        return '労働安全衛生関連法令'


def main():
    """メイン実行関数"""
    scraper = EnhancedSafetyLawScraper()
    
    # データ収集
    revisions = scraper.collect_all_data()
    
    # JSONに保存
    with open('revisions_list.json', 'w', encoding='utf-8') as f:
        json.dump(revisions, f, ensure_ascii=False, indent=2)
    
    print("\n処理が完了しました！")
    print(f"生成されたファイル: revisions_list.json ({len(revisions)}件)")


if __name__ == "__main__":
    main()
