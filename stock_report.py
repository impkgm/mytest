import datetime
import json
import os
import urllib.parse
import urllib.request
import webbrowser
import pandas as pd


def get_eastmoney_spot_data():
    print("正在通过系统原生底层通道请求东方财富接口...")

    # 1. 构造官方标准行情 URL (统一资源定位符)
    url = "https://82.push2.eastmoney.com/api/qt/clist/get"

    params = {
        "pn": "1",
        "pz": "200",  # 默认获取前200只股票（包含今日领涨的强势股）
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f2,f3,f4,f5,f6,f7,f8,f9,f12,f14",
    }

    # 编码参数
    full_url = f"{url}?{urllib.parse.urlencode(params)}"

    # 2. 伪装标准的真实浏览器头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/\*;q=0.8",
    }

    try:
        # 3. 使用 urllib.request 强制创建一个「不受 Python 环境变量干扰」的直连请求
        # empty_proxies = {} 代表不加载任何系统代理代理，像浏览器一样直出网络
        proxy_support = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_support)
        req = urllib.request.Request(full_url, headers=headers)

        # 发送请求并读取
        with opener.open(req, timeout=10) as response:
            html_bytes = response.read()
            json_data = json.loads(html_bytes.decode("utf-8"))

        if (
            json_data
            and "data" in json_data
            and "diff" in json_data["data"]
        ):
            raw_list = json_data["data"]["diff"]
        else:
            print("❌ 接口返回结构不匹配")
            return pd.DataFrame()

        # 4. 洗数据
        cleaned_data = []
        for item in raw_list:
            cleaned_data.append(
                {
                    "股票代码": item.get("f12", "-"),
                    "股票名称": item.get("f14", "-"),
                    "最新价": item.get("f2", "-"),
                    "涨跌幅": (
                        f"{item['f3']:.2f}%"
                        if isinstance(item.get("f3"), (int, float))
                        else "-"
                    ),
                    "涨跌额": item.get("f4", "-"),
                    "成交量(手)": item.get("f5", "-"),
                    "成交额(元)": item.get("f6", "-"),
                    "换手率": (
                        f"{item['f8']:.2f}%"
                        if isinstance(item.get("f8"), (int, float))
                        else "-"
                    ),
                    "市盈率-动态": item.get("f9", "-"),
                }
            )

        return pd.DataFrame(cleaned_data)

    except Exception as e:
        print(f"❌ 物理直连通道请求失败: {e}")
        return pd.DataFrame()


def generate_html_report():
    df_stocks = get_eastmoney_spot_data()

    if df_stocks.empty:
        print("\n❌ 错误：依旧无法获取数据。")
        print(
            "这说明你的科学上网软件开启了系统全局 TUN 虚拟网卡模式，切断了本地所有编程语言的直连回路。"
        )
        print("【终极解决办法】：请在右下角托盘彻底『退出(Quit)』科学上网软件后再运行。")
        return

    current_month = datetime.datetime.now().strftime("%Y年%m月")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{current_month} A股实时交易行情盘点</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background-color: #f8f9fa; }}
            h1, h2 {{ color: #2c3e50; border-bottom: 2px solid #34495e; padding-bottom: 10px; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px 15px; text-align: left; }}
            th {{ background-color: #34495e; color: white; position: sticky; top: 0; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #e9ecef; }}
            .positive {{ color: #e74c3c; font-weight: bold; }}
            .negative {{ color: #27ae60; font-weight: bold; }}
            .scroll-table {{ max-height: 700px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 A股个股行情快照 ({current_month})</h1>
            <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="scroll-table">
                {df_stocks.to_html(index=False, classes='stocks-table')}
            </div>
        </div>
        <script>
            document.querySelectorAll('td').forEach(td => {{
                if (td.innerText.includes('%')) {{
                    let val = parseFloat(td.innerText);
                    if (val > 0) {{
                        td.classList.add('positive');
                        td.innerText = '+' + td.innerText;
                    }} else if (val < 0) {{
                        td.classList.add('negative');
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    file_name = "A_share_direct_report.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"报告生成成功: {file_name}")
    webbrowser.open(f"file://{os.path.abspath(file_name)}")
    print("已成功在浏览器中打开报告！")


if __name__ == "__main__":
    generate_html_report()