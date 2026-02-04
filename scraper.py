#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
労働安全衛生法令改正追跡システム - e-Gov API版スクレイパー
正確な法改正情報を収集
"""

import requests
import json
import time
import re
import feedparser
import xml.etree.ElementTree as ET
import urllib.parse
from typing import Dict, List
from datetime import datetime, date, timedelta

class EgovAPIScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 労働安全衛生関連の法令を識別する正規表現
        self.safety_regex = re.compile(
            r"(労働安全衛生|安全衛生|労災|じん肺|作業環境|"
            r"化学物質|特定化学物質|有機溶剤|粉じん|石綿|鉛|"
            r"酸素欠乏|電離放射線|高気圧|ボイラー|クレーン|"
            r"労働基準|労働契約)"
        )
    
    def clean_html(self, text: str) -> str:
        """HTMLタグを削除してクリーンなテキストに"""
        if not text:
            return ""
        # HTMLタグを削除
        text = re.sub(r'<[^>]+>', ' ', text)
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_feed(self, url: str):
        """RSSフィードを確実に取得"""
        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            
            # 失敗を可視化
            if getattr(feed, "bozo", 0):
                print(f"  [警告] feedparser bozo: {feed.bozo_exception}")
            
            entries_count = len(getattr(feed, "entries", []))
            print(f"  取得: {entries_count}件")
            return feed
        except Exception as e:
            print(f"  エラー: {e}")
            return feedparser.FeedParserDict()
    
    def fetch_egov_updated_laws(self, lookback_days: int = 7) -> List[Dict]:
        """e-Gov 更新法令一覧API から直近N日分を取得"""
        print("\n[e-Gov API] 更新法令一覧")
        print("-" * 60)
        
        revisions = []
        
        for i in range(lookback_days + 1):
            d = (date.today() - timedelta(days=i)).strftime("%Y%m%d")
            url = f"https://laws.e-gov.go.jp/api/1/updatelawlists/{d}"
            
            try:
                r = requests.get(url, headers=self.headers, timeout=20)
                if r.status_code != 200:
                    continue
                
                root = ET.fromstring(r.text)
                code = root.findtext(".//Result/Code", default="1")
                if code != "0":
                    continue
                
                for info in root.findall(".//LawNameListInfo"):
                    law_name = info.findtext("LawName", default="").strip()
                    if not law_name or not self.safety_regex.search(law_name):
                        continue
                    
                    enforcement = info.findtext("EnforcementDate", default="").strip()
                    promulg = info.findtext("PromulgationDate", default="").strip()
                    amend_name = info.findtext("AmendName", default="").strip()
                    law_no = info.findtext("LawNo", default="").strip()
                    
                    # 日付をYYYY-MM-DD形式に変換
                    promulg_date = ""
                    if promulg and len(promulg) == 8:
                        promulg_date = f"{promulg[:4]}-{promulg[4:6]}-{promulg[6:]}"
                    
                    enf_date = ""
                    if enforcement and len(enforcement) == 8:
                        enf_date = f"{enforcement[:4]}-{enforcement[4:6]}-{enforcement[6:]}"
                    
                    # 施行日があれば「施行予定」、なければ「公布済み」
                    stage = "enforcement_scheduled" if enforcement else "promulgated"
                    if enforcement:
                        # 施行日が過去なら「施行済み」
                        try:
                            enf_datetime = datetime.strptime(enforcement, "%Y%m%d")
                            if enf_datetime < datetime.now():
                                stage = "enforced"
                        except:
                            pass
                    
                    # 法令番号から詳細ページURLを生成
                    detail_url = "https://laws.e-gov.go.jp/"
                    if law_no:
                        # 法令番号をURLエンコード（例：昭和四十七年労働省令第三十二号）
                        import urllib.parse
                        encoded_no = urllib.parse.quote(law_no)
                        detail_url = f"https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/viewContents?lawId={encoded_no}"
                    
                    revisions.append({
                        "title": law_name,
                        "lawName": law_name,
                        "description": f"改正法令: {amend_name}" if amend_name else "法令更新",
                        "source": "e-Gov更新法令一覧API",
                        "stage": stage,
                        "publishedDate": f"{d[:4]}-{d[4:6]}-{d[6:8]}",
                        "officialUrl": detail_url,
                        "lawNo": law_no,
                        "promulgationDate": promulg_date,
                        "enforcementDate": enf_date,
                    })
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  {d}: {e}")
                continue
        
        print(f"  合計: {len(revisions)}件（安全衛生フィルタ後）")
        return revisions
    
    def fetch_egov_pubcom_rss(self) -> List[Dict]:
        """e-Gov パブリックコメント（労働カテゴリ）RSS"""
        print("\n[e-Gov] パブリックコメントRSS（労働カテゴリ）")
        print("-" * 60)
        
        # 労働カテゴリの意見募集RSS
        rss_url = "https://public-comment.e-gov.go.jp/rss/pcm_list_0000000046.xml"
        feed = self.parse_feed(rss_url)
        
        revisions = []
        for entry in feed.entries[:50]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            summary = entry.get("summary", "")
            
            # 労働安全衛生関連のみ
            if self.safety_regex.search(title) or self.safety_regex.search(summary):
                revisions.append({
                    "title": title,
                    "url": link,
                    "publishedDate": self.parse_date(published),
                    "source": "e-Govパブコメ（労働）",
                    "stage": "public_comment",
                    "description": self.clean_html(summary)[:300],
                })
        
        return revisions
    
    def fetch_kanpo_info(self) -> List[Dict]:
        """国立印刷局 官報情報を取得"""
        print("\n[官報] 国立印刷局")
        print("-" * 60)
        
        revisions = []
        
        # 官報検索サービスのRSS
        kanpo_rss_url = "https://kanpou.npb.go.jp/rss/kanpou.rss"
        
        try:
            feed = self.parse_feed(kanpo_rss_url)
            
            for entry in feed.entries[:100]:  # 最新100件
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                description = entry.get("description", "")
                
                # 労働安全衛生関連をフィルタ
                full_text = title + " " + description
                if not self.safety_regex.search(full_text):
                    continue
                
                # 公布・改正に関するキーワードでフィルタ
                if any(keyword in full_text for keyword in ['公布', '改正', '省令', '規則', '告示']):
                    revisions.append({
                        "title": title,
                        "url": link,
                        "publishedDate": self.parse_date(published),
                        "source": "官報",
                        "stage": "promulgated",
                        "description": self.clean_html(description)[:300],
                    })
            
            print(f"  取得: {len(revisions)}件（労働安全衛生フィルタ後）")
            return revisions
            
        except Exception as e:
            print(f"  エラー: {e}")
            return []
    
    def fetch_specific_topics(self) -> List[Dict]:
        """重要トピック（手動キュレーション）"""
        print("\n[手動キュレーション] 重要トピック")
        print("-" * 60)
        
        topics = [
            {
                "title": "高年齢労働者の安全衛生対策（エイジフレンドリーガイドライン）",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/newpage_00007.html",
                "stage": "enforced",
                "description": "60歳以上の高年齢労働者に対する安全衛生対策の実施を推進",
                "lawName": "労働安全衛生法",
            },
            {
                "title": "化学物質規制の見直し（第2段階・約850物質追加）",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html",
                "stage": "enforcement_scheduled",
                "description": "2026年4月から約850物質を追加し、合計約2,450物質に対してリスクアセスメント義務化",
                "lawName": "特定化学物質障害予防規則",
                "enforcementDate": "2026-04-01",
            },
            {
                "title": "石綿障害予防規則の改正",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyousei/anzen/sekimen/index.html",
                "stage": "enforced",
                "description": "石綿（アスベスト）の事前調査・報告の義務化",
                "lawName": "石綿障害予防規則",
            },
        ]
        
        revisions = []
        for topic in topics:
            revisions.append({
                "title": topic["title"],
                "officialUrl": topic["url"],
                "description": topic["description"],
                "source": "重要トピック",
                "stage": topic["stage"],
                "lawName": topic.get("lawName", "労働安全衛生関連"),
                "enforcementDate": topic.get("enforcementDate", ""),
            })
            print(f"  ✓ {topic['title']}")
        
        return revisions
    
    def parse_date(self, date_string: str) -> str:
        """日付文字列をパース"""
        try:
            if date_string:
                dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        return datetime.now().strftime('%Y-%m-%d')
    
    def collect_all_data(self) -> List[Dict]:
        """すべてのソースからデータを収集"""
        print("=" * 60)
        print("e-Gov API版スクレイパー開始")
        print("=" * 60)
        
        all_data = []
        
        # 1. e-Gov 更新法令一覧API（最も重要）
        updated_laws = self.fetch_egov_updated_laws(lookback_days=7)
        all_data.extend(updated_laws)
        
        # 2. e-Gov パブリックコメントRSS
        pubcom_data = self.fetch_egov_pubcom_rss()
        all_data.extend(pubcom_data)
        time.sleep(1)
        
        # 3. 官報情報
        kanpo_data = self.fetch_kanpo_info()
        all_data.extend(kanpo_data)
        time.sleep(1)
        
        # 4. 重要トピック（手動）
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
            
            # 重複除外
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            
            revision = {
                'id': idx,
                'lawName': item.get('lawName', '労働安全衛生関連法令'),
                'title': title,
                'stage': item.get('stage', 'consideration'),
                'description': item.get('description', '')[:300],
                'officialUrl': item.get('url') or item.get('officialUrl', ''),
                'source': item.get('source', 'e-Gov'),
                'collectedDate': datetime.now().strftime('%Y-%m-%d')
            }
            
            # 日付情報
            for date_field in ['publishedDate', 'promulgationDate', 'enforcementDate']:
                date_value = item.get(date_field)
                if date_value and date_value != "":
                    # YYYYMMDD形式の場合はYYYY-MM-DDに変換
                    if len(str(date_value)) == 8 and str(date_value).isdigit():
                        date_value = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}"
                    revision[date_field] = date_value
            
            revisions.append(revision)
        
        # ステージ別件数を表示
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
        for stage, count in sorted(stage_counts.items()):
            print(f"  {stage_names.get(stage, stage)}: {count}件")
        
        return revisions


def main():
    """メイン実行関数"""
    scraper = EgovAPIScraper()
    
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
