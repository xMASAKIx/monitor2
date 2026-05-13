import requests
import time
import threading
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "MSW Bot with Custom Images is Alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    # 加入 use_reloader=False 避免在 Render 上重複啟動線程
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- 設定區域 ---
PLAYER_MAP = {
    "20372100007473992": {"name": "蕾米&芙蘭", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/792/1753813913624.png"},
    "20372100004981518": {"name": "AWAWA", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/706/1749651958133.png"},
    "20372100003328034": {"name": "Coya奇術", "image": "https://mod-file.dn.nexoncdn.co.kr/profile/949/1778243422289.png"},
    "20372100000224166": {"name": "別時", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/246/1739416591406.png"},
    "20372001057320745": {"name": "MIKA", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/854/1766070535501.png"},
    "20372100005833987": {"name": "菲特", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/440/1757093677010.png"},
    "20372100005779084": {"name": "簡&卡媽", "image": "https://mod-file.dn.nexoncdn.co.kr/profile/951/1770739129110.png"},
    "20372100007840052": {"name": "惡魔狐", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/982/1757623973159.png"},
    "20372100007791322": {"name": "奶鱈", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/773/1758903318897.png"},
    "20372100008359961": {"name": "沖田作者", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/18/1777724572613.png"},
    "20372100002553986": {"name": "殺手兔作者", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/610/1777201020468.png"},
    "20372100006407090": {"name": "北極熊初音作者", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/7/1778050053104.png"},
    "20372100009098159": {"name": "哥倫比雅作者", "image": "https://mod-file.dn.nexoncdn.co.kr/shop/123/1777628265094.png"},
    "20372100009382026": {"name": "JOON", "image": "https://mod-file.dn.nexoncdn.co.kr/profile/315/1778431919948.png"},
    "20372100003462156": {"name": "ㄋㄍ奧米加", "https://mod-file.dn.nexoncdn.co.kr/shop/987/1778554167572.png"},
    "20372100001585009": {"name": "打手槍王", "https://mod-file.dn.nexoncdn.co.kr/shop/982/1744040914954.png"}
}

DEFAULT_IMAGE = "https://example.com/default.png"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497592013166608484/-bQDkOKmZBbxRMXwkmgQqrFsk4cdrtKIuKfVlxk81XeXwqalZ-9VliOuSC5wI1YMcuRT"

CHECK_INTERVAL = 15 # 建議調高，避免被 Nexon 封鎖 IP
API_URL_TEMPLATE = "https://mverse-api.nexon.com/social/v1/profile/{}"

last_known_data = {pid: {"is_online": None, "world_name": None} for pid in PLAYER_MAP.keys()}

def check_players():
    global last_known_data
    print(f"[{time.strftime('%H:%M:%S')}] 啟動掃描...")

    for pid, info in PLAYER_MAP.items():
        time.sleep(0.2) # 每個請求微小間隔，保護 IP
        try:
            name = info["name"]
            custom_image = info.get("image", DEFAULT_IMAGE)
            url = API_URL_TEMPLATE.format(pid)
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            data_root = response.json().get('data', {})
            
            is_online = (data_root.get('isOnline') == 1)
            world_name = data_root.get('worldName') 
            p_code = data_root.get('profileCode', '未知')
            
            prev = last_known_data[pid]

            # 首次啟動：存入資料但不發通知
            if prev["is_online"] is None:
                last_known_data[pid] = {"is_online": is_online, "world_name": world_name}
                continue

            should_notify = False
            status_msg = ""
            
            if is_online != prev["is_online"]:
                should_notify = True
                status_msg = "🟢 上線了！" if is_online else "🔴 下線了。"
            elif is_online and world_name != prev["world_name"]:
                should_notify = True
                status_msg = "🔄 切換世界"

            if should_notify:
                last_known_data[pid] = {"is_online": is_online, "world_name": world_name}
                current_world = world_name if world_name else "大廳或選單中"
                color = 3066993 if is_online else 15158332 
                
                description = f"玩家：**{name}**\n代碼：`{p_code}`\n狀態：**{status_msg}**"
                if is_online:
                    description += f"\n目前位置：`{current_world}`"

                payload = {
                    "embeds": [{
                        "title": "楓之谷發貨號動態",
                        "description": description,
                        "thumbnail": {"url": custom_image}, 
                        "color": color,
                        "footer": {"text": f"PPSN: {pid}"},
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                    }]
                }
                
                # 分流邏輯
                if pid in SPECIAL_PLAYERS:
                    requests.post(DISCORD_WEBHOOK_URL_PAKA, json=payload)
                    print(f"🚀 [dc2] 專屬通知: {name}")
                else:
                    requests.post(DISCORD_WEBHOOK_URL, json=payload)
                    print(f"📣 [dc1] 一般通知: {name}")

        except Exception as e:
            print(f"檢查 {pid} ({info['name']}) 出錯: {e}")

def main_loop():
    while True:
        # 確保 check_players 內部有 print("掃描中...") 以便觀察
        check_players()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 1. 啟動時先發一次訊息確認連線 (加入詳細診斷日誌)
    print("--- 正在嘗試發送啟動訊號到 Discord ---")
    try:
        # 加入 headers 模擬瀏覽器，並透過 response 變數捕捉回傳狀態
        response = requests.post(
            DISCORD_WEBHOOK_URL, 
            json={"content": "🤖 維京2號已自己掰開！"},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        
        if response.status_code == 204:
            print(f"✅ Discord 啟動訊號發送成功！(狀態碼: {response.status_code})")
        else:
            print(f"❌ Discord 拒絕請求，錯誤代碼: {response.status_code}")
            print(f"   回應內容: {response.text}")
            
    except Exception as e:
        print(f"💥 啟動訊號發送過程中發生異常: {e}")

    # 2. 啟動背景線程
    monitor_thread = threading.Thread(target=main_loop, daemon=True)
    monitor_thread.start()
    print("📡 後台監控線程已啟動，開始循環掃描。")

    # 3. 啟動 Web 服務 (Render 需要此服務來維持連線)
    print("🌐 正在啟動 Flask Web 服務...")
    run_web()
