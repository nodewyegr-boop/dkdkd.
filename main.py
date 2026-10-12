import asyncio
import json
import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_ID = 1488103702488154173
DATA_FILE = "database.json"


def load_data():
  if not os.path.exists(DATA_FILE):
    return {"devices": {}, "bans": [], "warnings": {}}
  with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


class DDoSSimModal(discord.ui.Modal, title="DDOS Attack Panel"):
  target = discord.ui.TextInput(
      label="1. IP - url (เป้าหมาย)",
      placeholder="example.com หรือ 1.2.3.4",
      required=True,
  )
  port = discord.ui.TextInput(
      label="2. Port (1-65535)", placeholder="80 หรือ 443", required=True
  )
  time_sec = discord.ui.TextInput(
      label="3. Time (สูงสุด250วิ)", placeholder="60", required=True
  )
  devices = discord.ui.TextInput(
      label="4. device (เครื่อง)", placeholder="1", required=True
  )

  async def on_submit(self, interaction: discord.Interaction):
    data = load_data()
    user_id_str = str(interaction.user.id)

    # ตรวจสอบการโดนแบน
    if interaction.user.id in data.get("bans", []):
      await interaction.response.send_message(
          "❌ คุณโดนแบนจากการใช้งานบอทนี้แล้ว!", ephemeral=True
      )
      return

    target_val = self.target.value.strip().lower()

    # ตรวจสอบ .th หรือ Local IP
    if ".th" in target_val or "127.0.0.1" in target_val or "localhost" in target_val:
      warnings = data.setdefault("warnings", {})
      user_warns = warnings.get(user_id_str, 0) + 1
      warnings[user_id_str] = user_warns

      if user_warns >= 3:
        if interaction.user.id not in data.get("bans", []):
          data.setdefault("bans", []).append(interaction.user.id)
        save_data(data)
        await interaction.response.send_message(
            f"❌ ห้ามยิง .th หรือ Local IP ไอ้เอ๋อ! เตือนรอบที่ {user_warns}"
            " คุณโดนแบนถาวรจากการใช้บอทแล้ว",
            ephemeral=True,
        )
      else:
        save_data(data)
        await interaction.response.send_message(
            f"⚠️ ห้ามยิง .th หรือ Local IP ไอ้เอ๋อ! เตือนรอบที่ {user_warns}/3",
            ephemeral=True,
        )
      return

    # ตรวจสอบตัวเลข
    try:
      req_devices = int(self.devices.value.strip())
      req_time = int(self.time_sec.value.strip())
    except ValueError:
      await interaction.response.send_message(
          "❌ กรุณากรอก Port, Time และ Device เป็นตัวเลขเท่านั้น!",
          ephemeral=True,
      )
      return

    if req_time > 250:
      req_time = 250

    # ตรวจสอบ Device ของผู้ใช้ (เริ่มต้นทุกคนมี 0 เครื่อง)
    user_devices = (
        data.get("devices", {}).get(user_id_str, {}).get("count", 0)
    )
    if req_devices > user_devices:
      await interaction.response.send_message(
          f"❌ ยิงไม่ได้! คุณมี Device ทั้งหมด {user_devices} เครื่อง"
          f" แต่กรอกไป {req_devices} เครื่อง",
          ephemeral=True,
      )
      return

    display_target = target_val
    display_url = (
        f"https://{target_val}"
        if not target_val.startswith("http")
        else target_val
    )

    # ส่ง Embed 2 ต่อ 2 (กำลังเริ่มยิง)
    embed = discord.Embed(
        title=(
            "<a:1000035744:1559183157532565524> **DDOS BY C**"
            " (SIMULATION)"
        ),
        color=discord.Color.from_rgb(255, 182, 193),  # สีชมพู
    )
    embed.add_field(
        name="<:1000038745:1559183912113148065> Target",
        value=f"{display_target} : {display_url}",
        inline=False,
    )
    embed.add_field(
        name="<:1000038746:1559184363021795369> Speed Web",
        value="กำลังเริ่มคำนวณความเร็ว...",
        inline=False,
    )
    embed.add_field(
        name="<:1000038748:1559185433458385019> Device",
        value=f"{req_devices} เครื่อง",
        inline=False,
    )
    embed.add_field(
        name="<:1000038748:1559185433458385019> Time",
        value=f"กำลังนับถอยหลัง {req_time} วินาที...",
        inline=False,
    )
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1488104101085577229/1559186792522190930/137316d06f5fe8f5a2b243c67919345f.jpg?ex=6ace295b&is=6accd7db&hm=0567a79045644d8d92cd84d2a9ccf48737e9ef19bce3acd1b00f66fb37946c2e&"
    )

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    # ลูปอัปเดตความเร็วทุก 3 วิ และนับถอยหลังเวลาทุก 1 วิ
    for remaining in range(req_time, 0, -1):
      await asyncio.sleep(1)
      speed_val = (
          f"{2000 + (req_time - remaining) * 75} req/s (DrDdos / TCP/UDP"
          " Flood)"
      )

      updated_embed = discord.Embed(
          title=(
              "<a:1000035744:1559183157532565524> **DDOS BY C**"
              " (SIMULATION)"
          ),
          color=discord.Color.from_rgb(255, 182, 193),
      )
      updated_embed.add_field(
          name="<:1000038745:1559183912113148065> Target",
          value=f"{display_target} : {display_url}",
          inline=False,
      )
      updated_embed.add_field(
          name="<:1000038746:1559184363021795369> Speed Web",
          value=speed_val,
          inline=False,
      )
      updated_embed.add_field(
          name="<:1000038748:1559185433458385019> Device",
          value=f"{req_devices} เครื่อง",
          inline=False,
      )
      updated_embed.add_field(
          name="<:1000038748:1559185433458385019> Time",
          value=f"เหลือเวลาอีก {remaining} วินาที",
          inline=False,
      )
      updated_embed.set_image(
          url="https://cdn.discordapp.com/attachments/1488104101085577229/1559186792522190930/137316d06f5fe8f5a2b243c67919345f.jpg?ex=6ace295b&is=6accd7db&hm=0567a79045644d8d92cd84d2a9ccf48737e9ef19bce3acd1b00f66fb37946c2e&"
      )
      try:
        await msg.edit(embed=updated_embed)
      except Exception:
        break


class DDoSSimView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="",
      style=discord.ButtonStyle.secondary,
      emoji="<a:1000038742:1559181609528205372>",
      custom_id="ddos_button_trigger",
  )
  async def trigger_button(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    data = load_data()
    if interaction.user.id in data.get("bans", []):
      await interaction.response.send_message(
          "❌ คุณโดนแบนจากการใช้งานบอทนี้แล้ว!", ephemeral=True
      )
      return
    await interaction.response.send_modal(DDoSSimModal())


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  bot.add_view(DDoSSimView())


@bot.command(name="ddos")
async def ddos_cmd(ctx):
  if ctx.author.id != ADMIN_ID:
    await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
    return

  embed = discord.Embed(
      title="<a:1000035910:1559173862820810803> DDOS ATTACK",
      color=discord.Color.from_rgb(255, 182, 193),  # สีชมพู
  )
  embed.description = (
      "<:1000035915:1559174417097953340> **หากสนใจกดTK มา**\n"
      "-. เรทราคา device ละ 65B TH รับเเค่ซองทรูมันนี่\n"
      "-. device สูงสุด 8 เครื่อง\n\n"
      "<a:1000038732:1559175829001338980> **กฎการใช้**\n"
      "-. ห้ามยิง .th หรือเว็บที่เกี่ยวกับรัฐ : หน่วยงาน\n"
      "-. ห้ามยิง Local IP พวกแบบ 127.0.0.1\n"
      "-. ถ้าโดนเตือนครบ 5 ครั้งจะโดนแบนไม่ให้ใช้\n\n"
      "<:1000038740:1559179488389242950> **สามารถยิงได้:เบื้องต้น**\n"
      "-. ยิงห้องเสียงดิสได้\n"
      "-. เว็บต่างๆ พวกแบบ .com หรืออะไรต่างๆ ได้\n"
      "-. เซิฟเกมต่างๆ เช่น ฟีฟาย โรบอค\n\n"
      "<a:1000035726:1559180464487407707> มี Ddos แจกฟรีให้ใช้ 3 ชม ทุก 3 วัน"
      " นะงับ"
  )
  embed.set_image(
      url="https://cdn.discordapp.com/attachments/1488104101085577229/1559181189175312466/ef8e34b79db57b50c3c29471d10c4eef.jpg?ex=6ace2423&is=6accd2a3&hm=b1d5fc7fc89993d53008fa4e8aed6311579ce453741c7e29015c5c7d9ffe95e2&"
  )

  await ctx.send(embed=embed, view=DDoSSimView())


@bot.command(name="device")
async def device_cmd(ctx, member: discord.Member = None, amount_str: str = None):
  if ctx.author.id != ADMIN_ID:
    await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
    return

  if not member or not amount_str:
    await ctx.send(
        "❌ ตัวอย่างคำสั่ง: `!device @user +2` หรือ `!device @user -1`"
    )
    return

  data = load_data()
  user_id_str = str(member.id)
  user_data = data.setdefault("devices", {}).setdefault(
      user_id_str, {"count": 0}
  )

  try:
    if amount_str.startswith("+"):
      val = int(amount_str[1:])
      user_data["count"] += val
    elif amount_str.startswith("-"):
      val = int(amount_str[1:])
      user_data["count"] = max(0, user_data["count"] - val)
    else:
      val = int(amount_str)
      user_data["count"] += val

    save_data(data)
    await ctx.send(
        f"✅ อัปเดต Device ให้ {member.mention} สำเร็จ! จำนวนปัจจุบัน:"
        f" {user_data['count']} เครื่อง"
    )
  except ValueError:
    await ctx.send("❌ รูปแบบจำนวน device ไม่ถูกต้อง!")


@bot.command(name="b")
async def ban_cmd(ctx, member: discord.Member = None):
  if ctx.author.id != ADMIN_ID:
    await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
    return
  if not member:
    await ctx.send("❌ กรุณา @User ที่ต้องการแบน")
    return

  data = load_data()
  bans = data.setdefault("bans", [])
  if member.id not in bans:
    bans.append(member.id)
    save_data(data)
    await ctx.send(f"✅ แบน {member.mention} สำเร็จ")
  else:
    await ctx.send(f"⚠️ ผู้ใช้นี้โดนแบนอยู่แล้ว")


@bot.command(name="ub")
async def unban_cmd(ctx, member: discord.Member = None):
  if ctx.author.id != ADMIN_ID:
    await ctx.send("ชั้นต่ำอยากจะใช้คำสั่งชั้นสูงรั่ว5555")
    return
  if not member:
    await ctx.send("❌ กรุณา @User ที่ต้องการปลดแบน")
    return

  data = load_data()
  bans = data.setdefault("bans", [])
  if member.id in bans:
    bans.remove(member.id)
    save_data(data)
    await ctx.send(f"✅ ปลดแบน {member.mention} สำเร็จ")
  else:
    await ctx.send(f"⚠️ ผู้ใช้นี้ไม่ได้โดนแบน")


bot.run("YOUR_DISCORD_BOT_TOKEN")
