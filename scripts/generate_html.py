#!/usr/bin/env python3
"""
내부자 거래 대시보드 HTML 생성
"""

import json
from pathlib import Path

def format_amount(amount):
    """금액 포맷 (억원)"""
    billion = amount / 100_000_000
    if abs(billion) >= 1000:
        return f"{billion/10000:.1f}조"
    return f"{billion:.0f}억"

def generate_html():
    # 데이터 로드
    data_path = Path(__file__).parent.parent / "data" / "insider.json"
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    last_updated = data["lastUpdated"]
    summary = data["summary"]
    trades_json = json.dumps(data["trades"], ensure_ascii=False)
    hot_stocks_json = json.dumps(data["hotStocks"], ensure_ascii=False)
    big_players_json = json.dumps(data["bigPlayers"], ensure_ascii=False)
    sector_json = json.dumps(data["sectorSentiment"], ensure_ascii=False)
    daily_json = json.dumps(data["dailyData"], ensure_ascii=False)
    
    net_amount_str = format_amount(summary["net_amount"])
    total_buy_str = format_amount(summary["total_buy"])
    total_sell_str = format_amount(summary["total_sell"])
    
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>코스피 200 내부자 거래</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: #000; 
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        
        .header {{ margin-bottom: 24px; }}
        .title {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
        .subtitle {{ font-size: 13px; color: #6b7280; }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            background: #111;
            border-radius: 12px;
            padding: 20px;
        }}
        .card-label {{ font-size: 12px; color: #6b7280; margin-bottom: 8px; }}
        .card-value {{ font-size: 28px; font-weight: 700; }}
        .card-value.positive {{ color: #22c55e; }}
        .card-value.negative {{ color: #ef4444; }}
        .card-sub {{ font-size: 12px; color: #9ca3af; margin-top: 4px; }}
        
        .filters {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .filter-group {{
            display: flex;
            gap: 4px;
            background: #111;
            padding: 4px;
            border-radius: 8px;
        }}
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            background: transparent;
            color: #9ca3af;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{ color: #fff; }}
        .filter-btn.active {{ background: #3b82f6; color: #fff; }}
        
        .chart-section {{
            background: #111;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chart-container {{
            height: 300px;
        }}
        
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}
        
        .list-section {{
            background: #111;
            border-radius: 12px;
            padding: 20px;
        }}
        .list-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #222;
        }}
        .list-item:last-child {{ border-bottom: none; }}
        .list-rank {{
            width: 24px;
            font-size: 12px;
            color: #6b7280;
            font-weight: 600;
        }}
        .list-info {{
            flex: 1;
            margin-left: 12px;
        }}
        .list-name {{ font-weight: 600; font-size: 14px; }}
        .list-sub {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
        .list-value {{
            font-weight: 700;
            font-size: 14px;
        }}
        .list-value.positive {{ color: #22c55e; }}
        .list-value.negative {{ color: #ef4444; }}
        
        .sector-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }}
        .sector-card {{
            background: #1a1a1a;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .sector-name {{ font-size: 13px; font-weight: 500; margin-bottom: 8px; }}
        .sector-value {{ font-size: 18px; font-weight: 700; }}
        .sector-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }}
        .sector-indicator.bullish {{ background: #22c55e; }}
        .sector-indicator.bearish {{ background: #ef4444; }}
        .sector-indicator.neutral {{ background: #6b7280; }}
        
        .table-section {{
            background: #111;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        .table-header {{
            padding: 16px 20px;
            border-bottom: 1px solid #222;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .table-scroll {{
            max-height: 400px;
            overflow-y: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 12px 16px;
            font-size: 11px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            border-bottom: 1px solid #222;
            position: sticky;
            top: 0;
            background: #111;
        }}
        td {{
            padding: 12px 16px;
            font-size: 13px;
            border-bottom: 1px solid #1a1a1a;
        }}
        tr:hover {{ background: #0a0a0a; }}
        .type-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .type-badge.buy {{ background: #14532d; color: #22c55e; }}
        .type-badge.sell {{ background: #7f1d1d; color: #ef4444; }}
        .type-badge.other {{ background: #1f2937; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">📊 코스피 200 내부자 거래</h1>
            <p class="subtitle">마지막 업데이트: {last_updated} · 최근 3개월 데이터</p>
        </div>
        
        <div class="summary-cards">
            <div class="summary-card">
                <div class="card-label">전체 순매수</div>
                <div class="card-value {"positive" if summary["net_amount"] >= 0 else "negative"}">{("+" if summary["net_amount"] >= 0 else "") + net_amount_str}원</div>
                <div class="card-sub">매수 {total_buy_str} / 매도 {total_sell_str}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">매수 우위 종목</div>
                <div class="card-value positive">{summary["buy_stocks"]}개</div>
                <div class="card-sub">순매수 > 0</div>
            </div>
            <div class="summary-card">
                <div class="card-label">매도 우위 종목</div>
                <div class="card-value negative">{summary["sell_stocks"]}개</div>
                <div class="card-sub">순매수 &lt; 0</div>
            </div>
            <div class="summary-card">
                <div class="card-label">총 거래 건수</div>
                <div class="card-value" style="color: #fff;">{summary["total_trades"]}건</div>
                <div class="card-sub">3개월 누적</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <button class="filter-btn" data-period="1W">1주</button>
                <button class="filter-btn" data-period="1M">1개월</button>
                <button class="filter-btn active" data-period="3M">3개월</button>
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-type="all">전체</button>
                <button class="filter-btn" data-type="buy">매수</button>
                <button class="filter-btn" data-type="sell">매도</button>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="section-title">📈 일별 매수/매도 추이</div>
            <div class="chart-container">
                <canvas id="dailyChart"></canvas>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="list-section">
                <div class="section-title">🔥 Hot Stocks</div>
                <div id="hot-stocks-list"></div>
            </div>
            <div class="list-section">
                <div class="section-title">👤 Big Players</div>
                <div id="big-players-list"></div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="section-title">🏢 섹터별 Sentiment</div>
            <div class="sector-grid" id="sector-grid"></div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <div class="section-title" style="margin: 0;">📋 상세 거래 내역</div>
                <input type="text" id="search-input" placeholder="종목명 검색..." style="
                    background: #1a1a1a;
                    border: 1px solid #333;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: #fff;
                    font-size: 13px;
                    width: 200px;
                ">
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>날짜</th>
                            <th>종목</th>
                            <th>내부자</th>
                            <th>직위</th>
                            <th>유형</th>
                            <th>수량</th>
                            <th>금액</th>
                        </tr>
                    </thead>
                    <tbody id="trades-table"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const TRADES = {trades_json};
        const HOT_STOCKS = {hot_stocks_json};
        const BIG_PLAYERS = {big_players_json};
        const SECTORS = {sector_json};
        const DAILY_DATA = {daily_json};
        
        let currentPeriod = '3M';
        let currentType = 'all';
        let searchQuery = '';
        let chart = null;
        
        // 금액 포맷
        function formatAmount(amount) {{
            const billion = Math.abs(amount) / 100000000;
            const sign = amount >= 0 ? '+' : '-';
            if (billion >= 10000) {{
                return sign + (billion / 10000).toFixed(1) + '조';
            }}
            return sign + billion.toFixed(0) + '억';
        }}
        
        // 날짜 필터
        function filterByPeriod(dateStr) {{
            const date = new Date(dateStr.slice(0, 4) + '-' + dateStr.slice(4, 6) + '-' + dateStr.slice(6, 8));
            const now = new Date();
            let daysAgo = 90;
            if (currentPeriod === '1W') daysAgo = 7;
            else if (currentPeriod === '1M') daysAgo = 30;
            const cutoff = new Date(now - daysAgo * 24 * 60 * 60 * 1000);
            return date >= cutoff;
        }}
        
        // 차트 렌더링
        function renderChart() {{
            const filtered = DAILY_DATA.filter(d => filterByPeriod(d.date));
            
            const labels = filtered.map(d => d.date.slice(4, 6) + '/' + d.date.slice(6, 8));
            const buyData = filtered.map(d => d.buy / 100000000);
            const sellData = filtered.map(d => -d.sell / 100000000);
            
            if (chart) {{
                chart.data.labels = labels;
                chart.data.datasets[0].data = buyData;
                chart.data.datasets[1].data = sellData;
                chart.update();
            }} else {{
                const ctx = document.getElementById('dailyChart').getContext('2d');
                chart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: labels,
                        datasets: [
                            {{
                                label: '매수',
                                data: buyData,
                                backgroundColor: '#22c55e',
                                borderRadius: 4,
                            }},
                            {{
                                label: '매도',
                                data: sellData,
                                backgroundColor: '#ef4444',
                                borderRadius: 4,
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top',
                                labels: {{ color: '#9ca3af', font: {{ size: 11 }} }}
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: (ctx) => ctx.dataset.label + ': ' + Math.abs(ctx.parsed.y).toFixed(0) + '억원'
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                grid: {{ color: '#222' }},
                                ticks: {{ color: '#6b7280', font: {{ size: 10 }} }}
                            }},
                            y: {{
                                grid: {{ color: '#222' }},
                                ticks: {{
                                    color: '#6b7280',
                                    font: {{ size: 10 }},
                                    callback: (v) => Math.abs(v) + '억'
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }}
        
        // Hot Stocks 렌더링
        function renderHotStocks() {{
            const container = document.getElementById('hot-stocks-list');
            container.innerHTML = HOT_STOCKS.slice(0, 10).map((stock, i) => `
                <div class="list-item">
                    <span class="list-rank">${{i + 1}}</span>
                    <div class="list-info">
                        <div class="list-name">${{stock.name}}</div>
                        <div class="list-sub">${{stock.count}}건</div>
                    </div>
                    <span class="list-value ${{stock.net_amount >= 0 ? 'positive' : 'negative'}}">
                        ${{formatAmount(stock.net_amount)}}원
                    </span>
                </div>
            `).join('');
        }}
        
        // Big Players 렌더링
        function renderBigPlayers() {{
            const container = document.getElementById('big-players-list');
            container.innerHTML = BIG_PLAYERS.slice(0, 10).map((player, i) => `
                <div class="list-item">
                    <span class="list-rank">${{i + 1}}</span>
                    <div class="list-info">
                        <div class="list-name">${{player.name}}</div>
                        <div class="list-sub">${{player.corp_name}} · ${{player.position}}</div>
                    </div>
                    <span class="list-value ${{player.type === '매수' ? 'positive' : 'negative'}}">
                        ${{player.type === '매수' ? '+' : '-'}}${{(player.amount / 100000000).toFixed(0)}}억
                    </span>
                </div>
            `).join('');
        }}
        
        // 섹터 렌더링
        function renderSectors() {{
            const container = document.getElementById('sector-grid');
            container.innerHTML = SECTORS.map(sector => `
                <div class="sector-card">
                    <div class="sector-name">
                        <span class="sector-indicator ${{sector.sentiment}}"></span>
                        ${{sector.sector}}
                    </div>
                    <div class="sector-value ${{sector.net_amount >= 0 ? 'positive' : 'negative'}}">
                        ${{formatAmount(sector.net_amount)}}
                    </div>
                </div>
            `).join('');
        }}
        
        // 테이블 렌더링
        function renderTable() {{
            let filtered = TRADES.filter(t => filterByPeriod(t.report_date));
            
            if (currentType === 'buy') {{
                filtered = filtered.filter(t => t.trade_type === '매수');
            }} else if (currentType === 'sell') {{
                filtered = filtered.filter(t => t.trade_type === '매도');
            }}
            
            if (searchQuery) {{
                filtered = filtered.filter(t => 
                    t.corp_name.toLowerCase().includes(searchQuery.toLowerCase())
                );
            }}
            
            const tbody = document.getElementById('trades-table');
            tbody.innerHTML = filtered.slice(0, 100).map(t => `
                <tr>
                    <td>${{t.report_date.slice(0, 4)}}-${{t.report_date.slice(4, 6)}}-${{t.report_date.slice(6, 8)}}</td>
                    <td><strong>${{t.corp_name}}</strong></td>
                    <td>${{t.insider_name}}</td>
                    <td>${{t.position}}</td>
                    <td><span class="type-badge ${{t.trade_type === '매수' ? 'buy' : t.trade_type === '매도' ? 'sell' : 'other'}}">${{t.trade_type}}</span></td>
                    <td>${{t.shares_change.toLocaleString()}}주</td>
                    <td>${{(t.amount / 100000000).toFixed(1)}}억</td>
                </tr>
            `).join('');
        }}
        
        // 필터 이벤트
        document.querySelectorAll('.filter-btn[data-period]').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn[data-period]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentPeriod = btn.dataset.period;
                renderChart();
                renderTable();
            }});
        }});
        
        document.querySelectorAll('.filter-btn[data-type]').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn[data-type]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentType = btn.dataset.type;
                renderTable();
            }});
        }});
        
        document.getElementById('search-input').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderTable();
        }});
        
        // 초기화
        renderChart();
        renderHotStocks();
        renderBigPlayers();
        renderSectors();
        renderTable();
    </script>
</body>
</html>'''
    
    output_path = Path(__file__).parent.parent / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML 생성 완료: {output_path}")


if __name__ == "__main__":
    generate_html()
