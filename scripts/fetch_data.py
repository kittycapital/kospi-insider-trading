#!/usr/bin/env python3
"""
코스피 200 내부자 거래 데이터 수집
Open DART API 사용
"""

import json
import os
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import time

# ============================================
# 설정
# ============================================

# API 키 (환경 변수에서 가져오기)
API_KEY = os.environ.get('DART_API_KEY', '')

# DART API URLs
CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
MAJOR_STOCK_URL = "https://opendart.fss.or.kr/api/majorstock.json"
ELE_STOCK_URL = "https://opendart.fss.or.kr/api/elestock.json"

# 코스피 200 주요 종목 (종목코드 -> 회사명, 섹터)
# 실제로는 더 많지만, 주요 종목 위주로 시작
KOSPI_200 = {
    "005930": {"name": "삼성전자", "sector": "반도체"},
    "000660": {"name": "SK하이닉스", "sector": "반도체"},
    "373220": {"name": "LG에너지솔루션", "sector": "2차전지"},
    "207940": {"name": "삼성바이오로직스", "sector": "바이오"},
    "005380": {"name": "현대차", "sector": "자동차"},
    "006400": {"name": "삼성SDI", "sector": "2차전지"},
    "035420": {"name": "NAVER", "sector": "IT"},
    "000270": {"name": "기아", "sector": "자동차"},
    "068270": {"name": "셀트리온", "sector": "바이오"},
    "035720": {"name": "카카오", "sector": "IT"},
    "028260": {"name": "삼성물산", "sector": "건설"},
    "012330": {"name": "현대모비스", "sector": "자동차"},
    "051910": {"name": "LG화학", "sector": "화학"},
    "066570": {"name": "LG전자", "sector": "전자"},
    "003670": {"name": "포스코홀딩스", "sector": "철강"},
    "055550": {"name": "신한지주", "sector": "금융"},
    "105560": {"name": "KB금융", "sector": "금융"},
    "096770": {"name": "SK이노베이션", "sector": "에너지"},
    "034730": {"name": "SK", "sector": "지주"},
    "015760": {"name": "한국전력", "sector": "유틸리티"},
    "017670": {"name": "SK텔레콤", "sector": "통신"},
    "030200": {"name": "KT", "sector": "통신"},
    "032830": {"name": "삼성생명", "sector": "보험"},
    "086790": {"name": "하나금융지주", "sector": "금융"},
    "316140": {"name": "우리금융지주", "sector": "금융"},
    "003550": {"name": "LG", "sector": "지주"},
    "033780": {"name": "KT&G", "sector": "소비재"},
    "018260": {"name": "삼성에스디에스", "sector": "IT"},
    "010130": {"name": "고려아연", "sector": "소재"},
    "009150": {"name": "삼성전기", "sector": "전자"},
    "024110": {"name": "기업은행", "sector": "금융"},
    "011200": {"name": "HMM", "sector": "운송"},
    "259960": {"name": "크래프톤", "sector": "게임"},
    "352820": {"name": "하이브", "sector": "엔터"},
    "036570": {"name": "엔씨소프트", "sector": "게임"},
    "251270": {"name": "넷마블", "sector": "게임"},
    "034020": {"name": "두산에너빌리티", "sector": "산업재"},
    "010950": {"name": "S-Oil", "sector": "에너지"},
    "090430": {"name": "아모레퍼시픽", "sector": "소비재"},
    "097950": {"name": "CJ제일제당", "sector": "식품"},
    "004020": {"name": "현대제철", "sector": "철강"},
    "011070": {"name": "LG이노텍", "sector": "전자"},
    "000810": {"name": "삼성화재", "sector": "보험"},
    "326030": {"name": "SK바이오팜", "sector": "바이오"},
    "302440": {"name": "SK바이오사이언스", "sector": "바이오"},
    "377300": {"name": "카카오페이", "sector": "핀테크"},
    "035900": {"name": "JYP Ent.", "sector": "엔터"},
    "041510": {"name": "에스엠", "sector": "엔터"},
    "003490": {"name": "대한항공", "sector": "운송"},
    "180640": {"name": "한진칼", "sector": "운송"},
    "047050": {"name": "포스코인터내셔널", "sector": "무역"},
    "010140": {"name": "삼성중공업", "sector": "조선"},
    "009540": {"name": "한국조선해양", "sector": "조선"},
    "329180": {"name": "HD현대중공업", "sector": "조선"},
    "267250": {"name": "HD현대", "sector": "지주"},
    "042700": {"name": "한미반도체", "sector": "반도체"},
    "005490": {"name": "POSCO", "sector": "철강"},
    "086280": {"name": "현대글로비스", "sector": "물류"},
    "161390": {"name": "한국타이어앤테크놀로지", "sector": "자동차"},
    "000100": {"name": "유한양행", "sector": "바이오"},
}

# corp_code 매핑 (stock_code -> corp_code)
# DART에서 다운로드한 데이터로 채워짐
CORP_CODE_MAP = {}


def download_corp_codes():
    """DART에서 기업 코드 다운로드"""
    global CORP_CODE_MAP
    
    print("📥 DART 기업 코드 다운로드 중...")
    
    try:
        url = f"{CORP_CODE_URL}?crtfc_key={API_KEY}"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"  ❌ 다운로드 실패: {response.status_code}")
            return False
        
        # ZIP 파일 압축 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            xml_content = zf.read('CORPCODE.xml')
        
        # XML 파싱
        root = ET.fromstring(xml_content)
        
        for corp in root.findall('.//list'):
            stock_code = corp.find('stock_code').text
            corp_code = corp.find('corp_code').text
            
            if stock_code and stock_code.strip():
                CORP_CODE_MAP[stock_code.strip()] = corp_code
        
        print(f"  ✅ {len(CORP_CODE_MAP)}개 기업 코드 로드 완료")
        return True
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return False


def fetch_insider_trading(corp_code, corp_name):
    """개별 기업 내부자 거래 조회"""
    
    trades = []
    
    # majorstock API 호출
    try:
        url = f"{MAJOR_STOCK_URL}?crtfc_key={API_KEY}&corp_code={corp_code}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == '000' and data.get('list'):
            for item in data['list']:
                trade = {
                    "corp_name": corp_name,
                    "corp_code": corp_code,
                    "report_date": item.get('rcept_dt', ''),
                    "insider_name": item.get('repror', ''),
                    "position": item.get('relate', ''),
                    "change_reason": item.get('report_resn', ''),
                    "shares_before": parse_number(item.get('stkqy_bsis', '0')),
                    "shares_after": parse_number(item.get('stkqy_aftn', '0')),
                    "shares_change": parse_number(item.get('stkqy_irds', '0')),
                }
                
                # 매수/매도 판단
                reason = trade['change_reason']
                if '매수' in reason or '취득' in reason:
                    trade['trade_type'] = '매수'
                elif '매도' in reason or '처분' in reason:
                    trade['trade_type'] = '매도'
                else:
                    trade['trade_type'] = '기타'
                
                trades.append(trade)
                
    except Exception as e:
        pass
    
    return trades


def parse_number(s):
    """문자열을 숫자로 변환"""
    if not s:
        return 0
    try:
        return int(s.replace(',', '').replace('-', '0'))
    except:
        return 0


def get_stock_price(stock_code):
    """주가 조회 (간단한 더미 데이터, 실제로는 API 필요)"""
    # 실제 구현 시 KRX, yfinance 등 사용
    # 여기서는 대략적인 주가 사용
    prices = {
        "005930": 72000,   # 삼성전자
        "000660": 180000,  # SK하이닉스
        "373220": 380000,  # LG에너지솔루션
        "207940": 780000,  # 삼성바이오로직스
        "005380": 210000,  # 현대차
        "006400": 420000,  # 삼성SDI
        "035420": 180000,  # NAVER
        "000270": 95000,   # 기아
        "068270": 180000,  # 셀트리온
        "035720": 40000,   # 카카오
    }
    return prices.get(stock_code, 50000)  # 기본값 5만원


def calculate_sentiment(trades):
    """Sentiment 계산"""
    total_buy_amount = 0
    total_sell_amount = 0
    buy_count = 0
    sell_count = 0
    
    for trade in trades:
        amount = abs(trade.get('shares_change', 0)) * trade.get('price', 50000)
        
        if trade['trade_type'] == '매수':
            total_buy_amount += amount
            buy_count += 1
        elif trade['trade_type'] == '매도':
            total_sell_amount += amount
            sell_count += 1
    
    net_amount = total_buy_amount - total_sell_amount
    
    return {
        "total_buy_amount": total_buy_amount,
        "total_sell_amount": total_sell_amount,
        "net_amount": net_amount,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "sentiment": "bullish" if net_amount > 0 else "bearish" if net_amount < 0 else "neutral"
    }


def main():
    print("=" * 60)
    print("🚀 내부자 거래 데이터 수집 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not API_KEY:
        print("❌ DART_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    # 기업 코드 다운로드
    if not download_corp_codes():
        print("❌ 기업 코드 다운로드 실패")
        return
    
    # 3개월 전 날짜
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
    
    # 모든 거래 데이터 수집
    all_trades = []
    sector_stats = defaultdict(lambda: {"buy": 0, "sell": 0, "count": 0})
    stock_stats = defaultdict(lambda: {"buy": 0, "sell": 0, "count": 0, "name": ""})
    daily_stats = defaultdict(lambda: {"buy": 0, "sell": 0})
    big_players = []
    
    print(f"\n📊 {len(KOSPI_200)}개 종목 데이터 수집 중...")
    
    for i, (stock_code, info) in enumerate(KOSPI_200.items()):
        corp_code = CORP_CODE_MAP.get(stock_code)
        
        if not corp_code:
            continue
        
        if (i + 1) % 10 == 0:
            print(f"  진행: {i + 1}/{len(KOSPI_200)}")
        
        trades = fetch_insider_trading(corp_code, info['name'])
        price = get_stock_price(stock_code)
        
        for trade in trades:
            trade['stock_code'] = stock_code
            trade['sector'] = info['sector']
            trade['price'] = price
            trade['amount'] = abs(trade.get('shares_change', 0)) * price
            
            # 3개월 이내 데이터만
            if trade['report_date'] >= three_months_ago:
                all_trades.append(trade)
                
                # 섹터별 통계
                sector = info['sector']
                if trade['trade_type'] == '매수':
                    sector_stats[sector]['buy'] += trade['amount']
                    stock_stats[stock_code]['buy'] += trade['amount']
                    daily_stats[trade['report_date']]['buy'] += trade['amount']
                elif trade['trade_type'] == '매도':
                    sector_stats[sector]['sell'] += trade['amount']
                    stock_stats[stock_code]['sell'] += trade['amount']
                    daily_stats[trade['report_date']]['sell'] += trade['amount']
                
                sector_stats[sector]['count'] += 1
                stock_stats[stock_code]['count'] += 1
                stock_stats[stock_code]['name'] = info['name']
                
                # Big Players
                if trade['amount'] >= 1_000_000_000:  # 10억 이상
                    big_players.append({
                        "name": trade['insider_name'],
                        "corp_name": trade['corp_name'],
                        "position": trade['position'],
                        "type": trade['trade_type'],
                        "amount": trade['amount'],
                        "date": trade['report_date']
                    })
        
        time.sleep(0.1)  # API 호출 제한
    
    print(f"  ✅ {len(all_trades)}건 거래 수집 완료")
    
    # Hot Stocks 계산
    hot_stocks = []
    for stock_code, stats in stock_stats.items():
        net = stats['buy'] - stats['sell']
        hot_stocks.append({
            "stock_code": stock_code,
            "name": stats['name'],
            "net_amount": net,
            "buy_amount": stats['buy'],
            "sell_amount": stats['sell'],
            "count": stats['count'],
            "sentiment": "bullish" if net > 0 else "bearish" if net < 0 else "neutral"
        })
    
    hot_stocks.sort(key=lambda x: abs(x['net_amount']), reverse=True)
    
    # 섹터별 Sentiment
    sector_sentiment = []
    for sector, stats in sector_stats.items():
        net = stats['buy'] - stats['sell']
        sector_sentiment.append({
            "sector": sector,
            "net_amount": net,
            "buy_amount": stats['buy'],
            "sell_amount": stats['sell'],
            "count": stats['count'],
            "sentiment": "bullish" if net > 0 else "bearish" if net < 0 else "neutral"
        })
    
    sector_sentiment.sort(key=lambda x: x['net_amount'], reverse=True)
    
    # Big Players 정렬
    big_players.sort(key=lambda x: x['amount'], reverse=True)
    
    # 일별 데이터 정렬
    daily_data = [{"date": k, "buy": v['buy'], "sell": v['sell']} for k, v in sorted(daily_stats.items())]
    
    # 전체 통계
    total_buy = sum(t['amount'] for t in all_trades if t['trade_type'] == '매수')
    total_sell = sum(t['amount'] for t in all_trades if t['trade_type'] == '매도')
    buy_stocks = len([s for s in hot_stocks if s['sentiment'] == 'bullish'])
    sell_stocks = len([s for s in hot_stocks if s['sentiment'] == 'bearish'])
    
    # 결과 저장
    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "period": "3M",
        "summary": {
            "total_buy": total_buy,
            "total_sell": total_sell,
            "net_amount": total_buy - total_sell,
            "buy_stocks": buy_stocks,
            "sell_stocks": sell_stocks,
            "total_trades": len(all_trades),
            "sentiment": "bullish" if total_buy > total_sell else "bearish"
        },
        "trades": all_trades[:500],  # 최근 500건만
        "hotStocks": hot_stocks[:20],
        "bigPlayers": big_players[:20],
        "sectorSentiment": sector_sentiment,
        "dailyData": daily_data
    }
    
    output_path = Path(__file__).parent.parent / "data" / "insider.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ 완료!")
    print(f"📁 {output_path}")
    print(f"💰 순매수: {(total_buy - total_sell) / 100_000_000:.0f}억원")
    print("=" * 60)


if __name__ == "__main__":
    main()
