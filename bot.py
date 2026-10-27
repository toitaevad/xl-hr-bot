import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "role_id": None, 
            "log_channel_id": None, 
            "cmd_channel_id": None, 
            "title": "🏢 [XL GANG] แบบฟอร์มลงทะเบียนเข้าร่วมแก๊ง"
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def is_allowed_channel(ctx):
    config = load_config()
    cmd_channel_id = config.get("cmd_channel_id")
    
    if not cmd_channel_id:
        return True
    
    if ctx.channel.id == cmd_channel_id:
        return True
    
    cmd_channel = ctx.guild.get_channel(cmd_channel_id)
    ch_mention = cmd_channel.mention if cmd_channel else "ห้องที่กำหนดไว้"
    await ctx.send(f"⚠️ **[XL HR]** คำสั่งนี้ใช้งานได้เฉพาะในห้อง {ch_mention} เท่านั้นครับ", delete_after=10)
    return False

class XLRegistrationModal(discord.ui.Modal):
    def __init__(self, title_name):
        super().__init__(title=title_name[:45])

    first_name = discord.ui.TextInput(
        label="ชื่อ (ในเกม IC)",
        placeholder="เช่น สมชาย",
        required=True
    )
    last_name = discord.ui.TextInput(
        label="นามสกุล (ในเกม IC)",
        placeholder="เช่น ใจดี",
        required=True
    )
    phone_number = discord.ui.TextInput(
        label="เบอร์โทร IC",
        placeholder="เช่น 555-1234",
        max_length=20,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        role_id = config.get("role_id")
        log_channel_id = config.get("log_channel_id")

        if not role_id:
            await interaction.response.send_message("⚠️ **[XL HR System]** ระบบยังไม่ได้ตั้งค่า ยศตระกูล! กรุณาแจ้ง Admin", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ **[XL HR System]** ไม่พบบทบาทในเซิร์ฟเวอร์", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role)
        except discord.Forbidden:
            await interaction.response.send_message("❌ **[XL HR System]** บอทไม่มีสิทธิ์อนุมัติยศนี้ (ยศบอทต้องอยู่สูงกว่ายศที่จะแจก)", ephemeral=True)
            return

        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="🔥 [XL HR] รายงานข้อมูลสมาชิกใหม่ (IC)",
                    color=discord.Color.dark_red()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.add_field(name="👤 Discord User", value=interaction.user.mention, inline=False)
                embed.add_field(name="📌 ชื่อ (IC)", value=self.first_name.value, inline=True)
                embed.add_field(name="📌 นามสกุล (IC)", value=self.last_name.value, inline=True)
                embed.add_field(name="📞 เบอร์โทร IC", value=self.phone_number.value, inline=False)
                embed.set_footer(text="XL HR System • บันทึกข้อมูลสำเร็จ")
                await log_channel.send(embed=embed)

        await interaction.response.send_message(
            f"ยินดีต้อนรับเข้าสู่ครอบครัว **XL** ครับคุณ {interaction.user.mention}! 🎉\n"
            f"ฝ่าย HR ได้บันทึกข้อมูลและมอบยศ {role.mention} ให้คุณเรียบร้อยแล้ว!", 
            ephemeral=True
        )

class XLRoleButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 ลงทะเบียนข้อมูลเข้าแก๊ง XL", style=discord.ButtonStyle.danger, custom_id="xl_hr_apply_button")
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        await interaction.response.send_modal(XLRegistrationModal(config.get("title", "🏢 [XL GANG] แบบฟอร์มลงทะเบียน")))

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="สมาชิกแก๊ง XL | !config"))
    print(f"✅ บอท [XL HR] ออนไลน์เรียบร้อยแล้ว! (Logged in as {bot.user.name})")
    bot.add_view(XLRoleButtonView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setcmd(ctx, channel: discord.TextChannel):
    config = load_config()
    config["cmd_channel_id"] = channel.id
    save_config(config)
    await ctx.send(f"🏢 **[XL HR]** ตั้งค่าห้องสำหรับพิมพ์คำสั่งสำเร็จ: ต่อไปนี้ให้พิมพ์คำสั่งที่ {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setrole(ctx, role: discord.Role):
    if not await is_allowed_channel(ctx): return
    config = load_config()
    config["role_id"] = role.id
    save_config(config)
    await ctx.send(f"🏢 **[XL HR]** ตั้งค่ายศแก๊งสำเร็จ: ผู้ที่กรอกข้อมูลจะได้รับยศ {role.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setlog(ctx, channel: discord.TextChannel):
    if not await is_allowed_channel(ctx): return
    config = load_config()
    config["log_channel_id"] = channel.id
    save_config(config)
    await ctx.send(f"🏢 **[XL HR]** ตั้งค่าห้องเก็บประวัติสำเร็จ: ข้อมูลจะถูกส่งไปที่ {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def settitle(ctx, *, new_title: str):
    if not await is_allowed_channel(ctx): return
    config = load_config()
    config["title"] = new_title
    save_config(config)
    await ctx.send(f"🏢 **[XL HR]** อัปเดตหัวข้อใบสมัครเป็น: **{new_title}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def config(ctx):
    if not await is_allowed_channel(ctx): return
    cfg = load_config()
    role = ctx.guild.get_role(cfg.get("role_id")) if cfg.get("role_id") else "ยังไม่ได้ตั้งค่า"
    log_ch = ctx.guild.get_channel(cfg.get("log_channel_id")) if cfg.get("log_channel_id") else "ยังไม่ได้ตั้งค่า"
    cmd_ch = ctx.guild.get_channel(cfg.get("cmd_channel_id")) if cfg.get("cmd_channel_id") else "พิมพ์ได้ทุกห้อง (ยังไม่ล็อก)"
    
    embed = discord.Embed(title="⚙️ [XL HR] การตั้งค่าระบบปัจจุบัน", color=discord.Color.dark_red())
    embed.add_field(name="ยศแก๊งที่จะมอบให้", value=role.mention if isinstance(role, discord.Role) else role, inline=False)
    embed.add_field(name="ห้องส่งประวัติ (Log)", value=log_ch.mention if isinstance(log_ch, discord.TextChannel) else log_ch, inline=False)
    embed.add_field(name="ห้องป้อนคำสั่งบอท", value=cmd_ch.mention if isinstance(cmd_ch, discord.TextChannel) else cmd_ch, inline=False)
    embed.add_field(name="หัวข้อฟอร์ม", value=cfg.get("title"), inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def sendform(ctx):
    if not await is_allowed_channel(ctx): return
    cfg = load_config()
    embed = discord.Embed(
        title=cfg.get("title", "🏢 [XL GANG] แบบฟอร์มลงทะเบียนเข้าร่วมแก๊ง"),
        description=(
            "ยินดีต้อนรับเข้าสู่ตระกูล **XL**\n\n"
            "กรุณากดปุ่ม **'📝 ลงทะเบียนข้อมูลเข้าแก๊ง XL'** ด้านล่างเพื่อกรอกชื่อ-นามสกุล และเบอร์โทร IC\n"
            "เมื่อกรอกข้อมูลเรียบร้อยระบบจะมอบยศประจำแก๊งให้ทันทีครับ!"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="XL HR Department • ฝ่ายบริหารและจัดการบุคคล")
    await ctx.send(embed=embed, view=XLRoleButtonView())

@setcmd.error
@setrole.error
@setlog.error
@settitle.error
@sendform.error
@config.error
async def admin_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 **[XL HR]** คำสั่งนี้อนุญาตให้ใช้ได้เฉพาะ **หัวหน้าแก๊ง / Admin** เท่านั้นครับ")

TOKEN = os.getenv("DISCORD_TOKEN") or "ใส่_Token_ของคุณตรงนี้"
bot.run(TOKEN)