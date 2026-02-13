#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
労働安全衛生法令改正追跡システム - 完全版スクレイパー
すべてのデータソースを統合し、既存データとマージ

改修履歴:
  2026-02-13  対象法令26件の一覧を追加、マージ方式に変更、
              厚労省通知・通達ページ、審議会モニタリング、
              雇用保険法等の関連法を対象に拡張
"""

import requests
import json
import time
import re
import os
import hashlib
import feedparser
import xml.etree.ElementTree as ET
import urllib.parse
from typing import Dict, List, Optional, Set
from datetime import datetime, date, timedelta

# ========================================================================
# 対象法令一覧（26法令）
# Deep Researchで特定された追跡対象法令
# ========================================================================
TARGET_LAWS = {
    # 法律（4件）
    "労働基準法": "law",
    "労働安全衛生法": "law",
    "労働契約法": "law",
    "じん肺法": "law",
    # 施行令・規則（18件）
    "労働安全衛生規則": "rule",
    "ボイラー及び圧力容器安全規則": "rule",
    "クレーン等安全規則": "rule",
    "コンベヤ安全規則": "rule",
    "有機溶剤中毒予防規則": "rule",
    "鉛中毒予防規則": "rule",
    "四アルキル鉛中毒予防規則": "rule",
    "特定化学物質障害予防規則": "rule",
    "高気圧作業安全衛生規則": "rule",
    "電離放射線障害防止規則": "rule",
    "酸素欠乏症等防止規則": "rule",
    "事務所衛生基準規則": "rule",
    "粉じん障害防止規則": "rule",
    "労働安全衛生法及びこれに基づく命令に係る登録及び指定に関する省令": "rule",
    "機械等検定規則": "rule",
    "労働安全衛生コンサルタント規則": "rule",
    "石綿障害予防規則": "rule",
    "東日本大震災により生じた放射性物質により汚染された土壌等を除染するための業務等に係る電離放射線障害防止規則": "rule",
    # その他関連法（4件）
    "労働者災害補償保険法": "related",
    "作業環境測定法": "related",
    "雇用保険法": "related",
    "労働者派遣法": "related",
}

# 短縮名 → 正式名のマッピング（フィルタリング用）
LAW_SHORT_NAMES = {
    "安衛則": "労働安全衛生規則",
    "安衛法": "労働安全衛生法",
    "ボイラー則": "ボイラー及び圧力容器安全規則",
    "クレーン則": "クレーン等安全規則",
    "有機則": "有機溶剤中毒予防規則",
    "鉛則": "鉛中毒予防規則",
    "四鉛則": "四アルキル鉛中毒予防規則",
    "特化則": "特定化学物質障害予防規則",
    "高圧則": "高気圧作業安全衛生規則",
    "電離則": "電離放射線障害防止規則",
    "酸欠則": "酸素欠乏症等防止規則",
    "粉じん則": "粉じん障害防止規則",
    "石綿則": "石綿障害予防規則",
    "除染則": "東日本大震災により生じた放射性物質により汚染された土壌等を除染するための業務等に係る電離放射線障害防止規則",
    "作環法": "作業環境測定法",
    "労災保険法": "労働者災害補償保険法",
    "雇保法": "雇用保険法",
    "派遣法": "労働者派遣法",
}


class CompleteScraper:
    def __init__(self, existing_data_path: Optional[str] = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # 対象法令を識別する正規表現（26法令 + 関連キーワード）
        law_keywords = [
            # 法律名（正式名称から抽出）
            "労働安全衛生", "安全衛生", "労災", "じん肺", "作業環境",
            "化学物質", "特定化学物質", "有機溶剤", "粉じん", "石綿", "鉛",
            "酸素欠乏", "電離放射線", "高気圧", "ボイラー", "クレーン",
            "コンベヤ", "事務所衛生", "労働基準", "労働契約",
            # 関連法キーワード
            "雇用保険", "労働者派遣", "労働者災害補償",
            # 改正でよく使われる表現
            "リスクアセスメント", "安衛法", "安衛則", "特化則",
            "個人事業者", "一人親方", "ストレスチェック",
            "熱中症", "墜落", "感電", "保護具",
            "除染", "放射性物質",
        ]
        self.safety_regex = re.compile(
            r"(" + "|".join(re.escape(kw) for kw in law_keywords) + r")"
        )

        # 既存データの読み込み（マージ用）
        self.existing_data: List[Dict] = []
        self.existing_urls: Set[str] = set()
        self.existing_titles: Set[str] = set()
        self.max_existing_id = 0

        if existing_data_path and os.path.exists(existing_data_path):
            try:
                with open(existing_data_path, 'r', encoding='utf-8') as f:
                    self.existing_data = json.load(f)
                for item in self.existing_data:
                    if item.get('officialUrl'):
                        self.existing_urls.add(item['officialUrl'])
                    if item.get('title'):
                        self.existing_titles.add(item['title'])
                    if item.get('id', 0) > self.max_existing_id:
                        self.max_existing_id = item['id']
                print(f"既存データ読み込み: {len(self.existing_data)}件 (最大ID: {self.max_existing_id})")
            except Exception as e:
                print(f"既存データ読み込みエラー: {e}")

    def is_duplicate(self, title: str, url: str = "") -> bool:
        """既存データとの重複チェック"""
        if url and url in self.existing_urls:
            return True
        if title and title in self.existing_titles:
            return True
        return False

    def clean_html(self, text: str) -> str:
        """HTMLタグを削除"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse_feed(self, url: str):
        """RSSフィードを確実に取得"""
        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            r.raise_for_status()
            feed = feedparser.parse(r.content)

            if getattr(feed, "bozo", 0):
                print(f"  [警告] feedparser bozo: {feed.bozo_exception}")

            entries_count = len(getattr(feed, "entries", []))
            print(f"  取得: {entries_count}件")
            return feed
        except Exception as e:
            print(f"  エラー: {e}")
            return feedparser.FeedParserDict()

    def fetch_egov_law_api_v2(self, lookback_days: int = 30) -> List[Dict]:
        """e-Gov 法令API Version 2 - 更新法令一覧"""
        print("\n[e-Gov API v2] 更新法令一覧")
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

                    law_no = info.findtext("LawNo", default="").strip()
                    law_id = info.findtext("LawId", default="").strip()
                    enforcement = info.findtext("EnforcementDate", default="").strip()
                    promulg = info.findtext("PromulgationDate", default="").strip()
                    amend_name = info.findtext("AmendName", default="").strip()

                    # 日付変換
                    promulg_date = f"{promulg[:4]}-{promulg[4:6]}-{promulg[6:]}" if len(promulg) == 8 else ""
                    enf_date = f"{enforcement[:4]}-{enforcement[4:6]}-{enforcement[6:]}" if len(enforcement) == 8 else ""

                    # 施行状態を判定
                    stage = "promulgated"
                    if enforcement:
                        try:
                            enf_datetime = datetime.strptime(enforcement, "%Y%m%d")
                            stage = "enforced" if enf_datetime < datetime.now() else "enforcement_scheduled"
                        except:
                            stage = "enforcement_scheduled"

                    # 法令詳細URL（Version 2対応）
                    detail_url = f"https://elaws.e-gov.go.jp/document?lawid={law_id}" if law_id else "https://laws.e-gov.go.jp/"

                    revisions.append({
                        "title": law_name,
                        "lawName": law_name,
                        "lawNo": law_no,
                        "lawId": law_id,
                        "description": f"改正法令: {amend_name}" if amend_name else "法令更新",
                        "source": "e-Gov法令API v2",
                        "stage": stage,
                        "publishedDate": f"{d[:4]}-{d[4:6]}-{d[6:8]}",
                        "originalPromulgationDate": promulg_date,
                        "enforcementDate": enf_date,
                        "officialUrl": detail_url,
                    })

                time.sleep(0.5)

            except Exception as e:
                continue

        print(f"  合計: {len(revisions)}件")
        return revisions

    def parse_pubcom_description(self, summary: str) -> Dict:
        """パブコメのdescriptionから構造化データを抽出"""
        text = self.clean_html(summary)
        result = {}

        # 案の公示日
        m = re.search(r'案の公示日[：:]?\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})', text)
        if m:
            result['announcementDate'] = m.group(1).replace('/', '-')

        # 受付締切日時
        m = re.search(r'受付締切日時[：:]?\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})', text)
        if m:
            result['deadlineDate'] = m.group(1).replace('/', '-')

        # 問合せ先（所管省庁）
        m = re.search(r'問合せ先[（(]所管省庁[・･]部局名等[)）][：:]?\s*(.+?)(?:\s+電話|$)', text)
        if m:
            result['ministry'] = m.group(1).strip()

        # メタデータを除いた説明文を生成
        clean_desc = text
        for pattern in [
            r'案の公示日[：:]?\s*\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\s*',
            r'受付締切日時[：:]?\s*\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\s*\d{1,2}:\d{2}\s*',
            r'カテゴリー[：:]?\s*\S+\s*',
            r'問合せ先[（(]所管省庁[・･]部局名等[)）][：:]?\s*.+?(?:電話[：:]?\s*[\d\-]+\s*)',
            r'電話[：:]?\s*[\d\-]+\s*',
        ]:
            clean_desc = re.sub(pattern, '', clean_desc)
        clean_desc = clean_desc.strip()
        result['cleanDescription'] = clean_desc if clean_desc else ''

        return result

    def fetch_egov_pubcom_rss(self) -> List[Dict]:
        """e-Gov パブリックコメント（複数カテゴリ対応）"""
        print("\n[e-Gov] パブリックコメントRSS")
        print("-" * 60)

        # 複数のRSSカテゴリを検索（厚生労働省関連）
        rss_urls = [
            "https://public-comment.e-gov.go.jp/rss/pcm_list_0000000046.xml",  # 厚生労働省
            "https://public-comment.e-gov.go.jp/rss/pcm_list_0000000047.xml",
            "https://public-comment.e-gov.go.jp/rss/pcm_list_0000000048.xml",
            "https://public-comment.e-gov.go.jp/rss/pcm_list.xml",            # 全省庁
        ]

        revisions = []
        seen_links = set()

        for rss_url in rss_urls:
            print(f"  RSS取得中: {rss_url}")
            feed = self.parse_feed(rss_url)
            if not hasattr(feed, 'entries'):
                continue

            for entry in feed.entries[:100]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                summary = entry.get("summary", "")

                # 重複排除
                if link in seen_links:
                    continue

                if self.safety_regex.search(title) or self.safety_regex.search(summary):
                    seen_links.add(link)
                    parsed = self.parse_pubcom_description(summary)

                    item = {
                        "title": title,
                        "officialUrl": link,
                        "publishedDate": parsed.get('announcementDate', self.parse_date(published)),
                        "source": "e-Govパブコメ",
                        "stage": "public_comment",
                        "description": parsed.get('cleanDescription', self.clean_html(summary)[:300]),
                    }

                    if parsed.get('announcementDate'):
                        item['announcementDate'] = parsed['announcementDate']
                    if parsed.get('deadlineDate'):
                        item['deadlineDate'] = parsed['deadlineDate']
                    if parsed.get('ministry'):
                        item['ministry'] = parsed['ministry']

                    revisions.append(item)

            time.sleep(1)

        print(f"  パブコメ合計: {len(revisions)}件")
        return revisions

    def fetch_kanpo_gov(self) -> List[Dict]:
        """官報情報（非公式RSS）"""
        print("\n[官報] 官報RSS（非公式）")
        print("-" * 60)

        revisions = []

        try:
            # 官報RSS（非公式 - testkun08080氏のGitHubベース）
            kanpo_urls = [
                "https://testkun08080.github.io/kanpo-rss/feed.xml",
                "https://testkun08080.github.io/kanpo-rss/feed_toc.xml",
            ]

            feed = None
            for url in kanpo_urls:
                try:
                    feed = self.parse_feed(url)
                    if hasattr(feed, 'entries') and len(feed.entries) > 0:
                        print(f"  使用RSS: {url}")
                        break
                except:
                    continue

            if not feed or not hasattr(feed, 'entries'):
                print("  官報RSSが取得できませんでした。スキップします。")
                return []

            for entry in feed.entries[:100]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                description = entry.get("description", "") or entry.get("summary", "")

                full_text = title + " " + description
                if not self.safety_regex.search(full_text):
                    continue

                if any(kw in full_text for kw in ['公布', '改正', '省令', '規則', '告示']):
                    revisions.append({
                        "title": title,
                        "officialUrl": link,
                        "publishedDate": self.parse_date(published),
                        "source": "官報（非公式RSS）",
                        "stage": "promulgated",
                        "description": self.clean_html(description)[:300],
                    })

            print(f"  合計: {len(revisions)}件")
            return revisions

        except Exception as e:
            print(f"  エラー: {e}")
            print("  官報情報の取得をスキップします")
            return []

    def fetch_anzeninfo_mhlw(self) -> List[Dict]:
        """職場のあんぜんサイト - 法令改正一覧"""
        print("\n[厚労省] 職場のあんぜんサイト")
        print("-" * 60)

        url = "https://anzeninfo.mhlw.go.jp/information/horei.html"

        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            r.encoding = 'utf-8'

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')

            revisions = []

            # テーブルから法令改正情報を抽出
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    if not self.safety_regex.search(text):
                        continue

                    # リンクを探す
                    link_tag = row.find('a')
                    link = ""
                    if link_tag and link_tag.get('href'):
                        href = link_tag['href']
                        if href.startswith('http'):
                            link = href
                        else:
                            link = f"https://anzeninfo.mhlw.go.jp{href}"

                    title = cells[0].get_text(strip=True) if cells else text[:100]

                    revisions.append({
                        "title": title,
                        "officialUrl": link or url,
                        "source": "職場のあんぜんサイト",
                        "stage": "consideration",
                        "description": text[:300],
                    })

            print(f"  合計: {len(revisions)}件")
            return revisions

        except Exception as e:
            print(f"  エラー: {e}")
            return []

    def fetch_mhlw_special_pages(self) -> List[Dict]:
        """厚生労働省 特設ページ（手動キュレーション）"""
        print("\n[厚労省] 特設ページ")
        print("-" * 60)

        topics = [
            {
                "title": "高年齢労働者の安全衛生対策（エイジフレンドリーガイドライン）",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/newpage_00007.html",
                "stage": "enforced",
                "description": "60歳以上の高年齢労働者に対する安全衛生対策の実施を推進",
            },
            {
                "title": "化学物質規制の見直し（第2段階・約850物質追加）",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html",
                "stage": "enforcement_scheduled",
                "description": "2026年4月から約850物質を追加し、合計約2,450物質に対してリスクアセスメント義務化",
                "enforcementDate": "2026-04-01",
            },
            {
                "title": "石綿障害予防規則の改正",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyousei/anzen/sekimen/index.html",
                "stage": "enforced",
                "description": "石綿（アスベスト）の事前調査・報告の義務化",
            },
        ]

        revisions = []
        for topic in topics:
            revisions.append({
                "title": topic["title"],
                "officialUrl": topic["url"],
                "description": topic["description"],
                "source": "厚労省特設ページ",
                "stage": topic["stage"],
                "enforcementDate": topic.get("enforcementDate", ""),
            })
            print(f"  + {topic['title']}")

        return revisions

    def fetch_mhlw_notices(self) -> List[Dict]:
        """厚労省 通知・通達ページの監視（新規追加）"""
        print("\n[厚労省] 通知・通達ページ")
        print("-" * 60)

        revisions = []
        # 安全衛生部の通知一覧ページ
        notice_urls = [
            "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/an-eihou/index_00001.html",
            "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html",
            "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/anzeneisei03_00004.html",
        ]

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("  beautifulsoup4がインストールされていません。スキップします。")
            return []

        for page_url in notice_urls:
            try:
                r = requests.get(page_url, headers=self.headers, timeout=20)
                r.encoding = 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')

                # PDFリンク（通知・通達）を探す
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    text = a_tag.get_text(strip=True)

                    # PDFリンクで省令番号・通知を含むもの
                    if '.pdf' in href and self.safety_regex.search(text):
                        full_url = href if href.startswith('http') else f"https://www.mhlw.go.jp{href}"

                        if not self.is_duplicate(text, full_url):
                            revisions.append({
                                "title": text[:200],
                                "officialUrl": full_url,
                                "source": "厚労省通知",
                                "stage": "enforced",
                                "description": f"厚労省通知・通達: {text[:300]}",
                            })

                # 新着情報リスト内のリンクも確認
                for li in soup.find_all('li'):
                    text = li.get_text(strip=True)
                    if self.safety_regex.search(text) and any(kw in text for kw in ['省令', '告示', '通知', '通達', '改正']):
                        link_tag = li.find('a', href=True)
                        if link_tag:
                            href = link_tag['href']
                            full_url = href if href.startswith('http') else f"https://www.mhlw.go.jp{href}"
                            link_text = link_tag.get_text(strip=True)

                            if not self.is_duplicate(link_text, full_url):
                                revisions.append({
                                    "title": link_text[:200],
                                    "officialUrl": full_url,
                                    "source": "厚労省ページ",
                                    "stage": "enforced",
                                    "description": text[:300],
                                })

                time.sleep(1)

            except Exception as e:
                print(f"  エラー ({page_url}): {e}")
                continue

        print(f"  合計: {len(revisions)}件")
        return revisions

    def fetch_mhlw_councils(self) -> List[Dict]:
        """労政審・検討会の監視（新規追加）"""
        print("\n[厚労省] 審議会・検討会モニタリング")
        print("-" * 60)

        revisions = []

        # 審議会・検討会の一覧ページ
        council_urls = [
            # 安全衛生分科会
            "https://www.mhlw.go.jp/stf/shingi/shingi-rousei_126972.html",
            # 労働基準関係法制研究会
            "https://www.mhlw.go.jp/stf/newpage_49541.html",
            # 化学物質管理に関する検討会
            "https://www.mhlw.go.jp/stf/shingi/other-roudou_558815_00009.html",
        ]

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("  beautifulsoup4がインストールされていません。スキップします。")
            return []

        for page_url in council_urls:
            try:
                r = requests.get(page_url, headers=self.headers, timeout=20)
                r.encoding = 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')

                page_title = soup.title.get_text(strip=True) if soup.title else ""

                # 報告書・答申・建議のリンクを探す
                for a_tag in soup.find_all('a', href=True):
                    text = a_tag.get_text(strip=True)
                    href = a_tag['href']

                    if any(kw in text for kw in ['報告書', '答申', '建議', '取りまとめ', '概要']):
                        full_url = href if href.startswith('http') else f"https://www.mhlw.go.jp{href}"

                        if not self.is_duplicate(text, full_url):
                            revisions.append({
                                "title": text[:200],
                                "officialUrl": full_url,
                                "source": "審議会・検討会",
                                "stage": "under_review",
                                "description": f"{page_title}: {text[:300]}",
                            })

                time.sleep(1)

            except Exception as e:
                print(f"  エラー ({page_url}): {e}")
                continue

        print(f"  合計: {len(revisions)}件")
        return revisions

    def fetch_mhlw_employment_insurance(self) -> List[Dict]:
        """雇用保険法関連の改正監視（新規追加）"""
        print("\n[厚労省] 雇用保険法等の関連法")
        print("-" * 60)

        revisions = []

        urls = [
            "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000160564_00042.html",
            "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/koyou/koyouhoken/index_00013.html",
        ]

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("  beautifulsoup4がインストールされていません。スキップします。")
            return []

        for page_url in urls:
            try:
                r = requests.get(page_url, headers=self.headers, timeout=20)
                r.encoding = 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')

                for a_tag in soup.find_all('a', href=True):
                    text = a_tag.get_text(strip=True)
                    href = a_tag['href']

                    if any(kw in text for kw in ['雇用保険', '改正', '施行', '給付']):
                        full_url = href if href.startswith('http') else f"https://www.mhlw.go.jp{href}"

                        if not self.is_duplicate(text, full_url):
                            revisions.append({
                                "title": text[:200],
                                "lawName": "雇用保険法",
                                "officialUrl": full_url,
                                "source": "厚労省",
                                "stage": "enforced",
                                "description": text[:300],
                            })

                time.sleep(1)

            except Exception as e:
                print(f"  エラー ({page_url}): {e}")
                continue

        print(f"  合計: {len(revisions)}件")
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

    def generate_highlights(self, item: Dict) -> List[str]:
        """改正内容から要旨（ハイライト）を自動生成"""
        highlights = []
        title = item.get('title', '')
        desc = item.get('description', '')
        amend = item.get('description', '')
        source = item.get('source', '')

        if source == 'e-Govパブコメ':
            # パブコメはタイトルから改正内容を推測
            if '施行令' in title:
                highlights.append("労働安全衛生法施行令の改正")
            if '規則' in title and '施行令' not in title:
                highlights.append("労働安全衛生規則の改正")
            if '化学物質' in title or '化学物質' in desc:
                highlights.append("化学物質対策関連の改正")
            if 'クレーン' in title:
                highlights.append("クレーン等安全規則の改正")
            return highlights

        # 改正法令名からキーワードを抽出して具体的なポイントを生成
        if '安全衛生法及び作業環境測定法の一部を改正する法律' in amend:
            highlights.append("労働安全衛生法・作業環境測定法の改正に伴う関係省令の整備")
        if '有機溶剤中毒予防規則等の一部を改正する省令' in amend:
            highlights.append("化学物質管理の強化（有機溶剤、特化則等の改正）")
        if '電離放射線障害防止規則' in amend or '電離放射線' in title:
            highlights.append("放射線障害防止に関する規制の見直し")
            highlights.append("被ばく管理・測定に関する規定の改正")

        # 法令名から具体的な改定ポイントを追加
        law_name = item.get('lawName', '')
        law_specific = {
            '労働安全衛生規則': '安全衛生に関する基本規則の見直し',
            '有機溶剤中毒予防規則': '有機溶剤の取扱い基準・管理体制の見直し',
            '鉛中毒予防規則': '鉛関連業務の管理基準の見直し',
            '粉じん障害防止規則': '粉じん作業場の管理基準の見直し',
            '特定化学物質障害予防規則': '特定化学物質の管理基準・測定方法の見直し',
            '石綿障害予防規則': '石綿（アスベスト）関連規制の強化',
            '酸素欠乏症等防止規則': '酸素欠乏症防止の測定・管理基準の見直し',
            'クレーン等安全規則': 'クレーン等の安全基準の見直し',
            'ボイラー及び圧力容器安全規則': 'ボイラー・圧力容器の検査基準の見直し',
            '高気圧作業安全衛生規則': '高気圧作業の安全衛生基準の見直し',
            '四アルキル鉛中毒予防規則': '四アルキル鉛の取扱い規定の見直し',
            'じん肺法施行規則': 'じん肺健康診断等の規定の見直し',
            '作業環境測定法施行規則': '作業環境測定の方法・基準の見直し',
        }
        for key, detail in law_specific.items():
            if key in law_name and detail not in highlights:
                highlights.append(detail)
                break

        # 厚労省特設ページの場合は説明からハイライトを生成
        if source == '厚労省特設ページ':
            highlights = []  # リセット
            if '化学物質' in title:
                highlights.append("リスクアセスメント対象物質の大幅拡大")
                highlights.append("約850物質を追加し合計約2,450物質に")
            if 'エイジフレンドリー' in title:
                highlights.append("高年齢労働者への安全配慮措置")
                highlights.append("転倒防止、墜落防止等の対策強化")
            if '石綿' in title:
                highlights.append("建築物の解体・改修時の事前調査義務化")
                highlights.append("石綿含有建材の調査結果の報告義務")

        # 施行予定日をハイライトに追加
        enf_date = item.get('enforcementDate', '')
        if enf_date:
            highlights.append(f"施行予定日: {enf_date}")

        return highlights

    def collect_all_data(self) -> List[Dict]:
        """すべてのデータソースから収集"""
        print("=" * 60)
        print("完全版スクレイパー開始")
        print(f"対象法令: {len(TARGET_LAWS)}件")
        print("=" * 60)

        all_data = []

        # 1. e-Gov 法令API v2
        egov_data = self.fetch_egov_law_api_v2(lookback_days=30)
        all_data.extend(egov_data)

        # 2. e-Gov パブコメ
        pubcom_data = self.fetch_egov_pubcom_rss()
        all_data.extend(pubcom_data)
        time.sleep(1)

        # 3. 官報
        kanpo_data = self.fetch_kanpo_gov()
        all_data.extend(kanpo_data)
        time.sleep(1)

        # 4. 職場のあんぜんサイト
        anzen_data = self.fetch_anzeninfo_mhlw()
        all_data.extend(anzen_data)
        time.sleep(1)

        # 5. 厚労省特設ページ
        mhlw_data = self.fetch_mhlw_special_pages()
        all_data.extend(mhlw_data)
        time.sleep(1)

        # 6. 厚労省 通知・通達ページ（新規）
        notice_data = self.fetch_mhlw_notices()
        all_data.extend(notice_data)
        time.sleep(1)

        # 7. 審議会・検討会（新規）
        council_data = self.fetch_mhlw_councils()
        all_data.extend(council_data)
        time.sleep(1)

        # 8. 雇用保険法等の関連法（新規）
        employment_data = self.fetch_mhlw_employment_insurance()
        all_data.extend(employment_data)

        print("\n" + "=" * 60)
        print(f"新規収集: {len(all_data)}件")
        print("=" * 60)

        return all_data

    def generate_revision_list(self, raw_data: List[Dict]) -> List[Dict]:
        """収集データを既存データとマージして整形"""
        # 既存データをベースにする
        revisions = list(self.existing_data)
        seen_titles = set(self.existing_titles)
        seen_urls = set(self.existing_urls)
        next_id = self.max_existing_id + 1
        new_count = 0

        for item in raw_data:
            title = item.get('title', '').strip()
            url = item.get('officialUrl', '').strip()

            if not title:
                continue

            # 重複チェック（タイトルとURLの両方）
            if title in seen_titles:
                continue
            if url and url in seen_urls:
                continue

            seen_titles.add(title)
            if url:
                seen_urls.add(url)

            revision = {
                'id': next_id,
                'lawName': item.get('lawName', '労働安全衛生関連法令'),
                'title': title,
                'stage': item.get('stage', 'consideration'),
                'description': item.get('description', '')[:300],
                'officialUrl': url,
                'source': item.get('source', ''),
                'collectedDate': datetime.now().strftime('%Y-%m-%d')
            }

            # 日付情報
            for date_field in ['publishedDate', 'originalPromulgationDate', 'enforcementDate']:
                date_value = item.get(date_field)
                if date_value and date_value != "":
                    if len(str(date_value)) == 8 and str(date_value).isdigit():
                        date_value = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}"
                    revision[date_field] = date_value

            # 法令ID
            if item.get('lawId'):
                revision['lawId'] = item['lawId']
            if item.get('lawNo'):
                revision['lawNo'] = item['lawNo']

            # パブコメ追加フィールド
            for extra_field in ['announcementDate', 'deadlineDate', 'ministry']:
                if item.get(extra_field):
                    revision[extra_field] = item[extra_field]

            # 要旨（ハイライト）を自動生成
            highlights = self.generate_highlights(item)
            if highlights:
                revision['highlights'] = highlights

            revisions.append(revision)
            next_id += 1
            new_count += 1

        # ステージ別件数
        stage_counts = {}
        for rev in revisions:
            stage = rev['stage']
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        print(f"\n既存データ: {len(self.existing_data)}件")
        print(f"新規追加: {new_count}件")
        print(f"合計: {len(revisions)}件")

        print("\nステージ別件数:")
        stage_names = {
            'consideration': '検討段階',
            'under_review': '検討段階',
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
    """メイン実行"""
    # 既存データパス
    existing_path = "public/data/revisions.json"

    scraper = CompleteScraper(existing_data_path=existing_path)

    # データ収集
    raw_data = scraper.collect_all_data()

    # マージして改正リスト生成
    revisions = scraper.generate_revision_list(raw_data)

    # JSONに保存
    os.makedirs("public/data", exist_ok=True)
    output_path = "public/data/revisions.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(revisions, f, ensure_ascii=False, indent=2)

    print(f"\n処理完了: {len(revisions)}件")
    print(f"ファイル: {output_path}")


if __name__ == "__main__":
    main()
