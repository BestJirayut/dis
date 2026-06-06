"""
Discord Announcement Bot
========================
บอทสำหรับสร้างประกาศแบบสวยงาม รองรับการลงรูป เลือกสีได้
ใช้คำสั่ง /announce แล้วกรอกข้อมูลผ่านหน้าต่าง (Modal)

Author: Jirayut0021
"""

import os
import re
import logging

import discord
from discord import app_commands
from discord.ext import commands

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("announce-bot")

# ---------------------------------------------------------------------------
# สีสำเร็จรูป (preset colors) — แสดงเป็นเมนูให้เลือก
# ---------------------------------------------------------------------------
PRESET_COLORS = {
    "น้ำเงิน (Discord)": 0x5865F2,
    "แดง":               0xED4245,
    "เขียว":             0x57F287,
    "เหลือง":            0xFEE75C,
    "ทอง":               0xF1C40F,
    "ส้ม":               0xE67E22,
    "ม่วง":              0x9B59B6,
    "ชมพู":              0xEB459E,
    "ฟ้าคราม":           0x1ABC9C,
    "ดำ":                0x2B2D31,
    "ขาว":               0xFFFFFF,
}

HEX_PATTERN = re.compile(r"^#?([0-9a-fA-F]{6})$")


def parse_color(text: str | None) -> int | None:
    """แปลงข้อความสีเป็นค่า int ของ discord.Color

    รองรับทั้ง:
      - ชื่อสีสำเร็จรูป (เช่น "แดง", "เขียว")
      - รหัส hex (เช่น "#5865F2" หรือ "5865F2")
    คืน None ถ้าแปลงไม่ได้
    """
    if not text:
        return None
    text = text.strip()

    # ลองจับคู่ชื่อสีสำเร็จรูปก่อน (ไม่สนตัวพิมพ์/ช่องว่าง)
    for name, value in PRESET_COLORS.items():
        if text == name or text.lower() == name.lower():
            return value

    # ลอง hex code
    match = HEX_PATTERN.match(text)
    if match:
        return int(match.group(1), 16)

    return None


def is_valid_url(url: str | None) -> bool:
    """ตรวจว่าเป็น URL รูปภาพที่ใช้ได้กับ embed หรือไม่"""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


# ---------------------------------------------------------------------------
# Modal — หน้าต่างกรอกข้อมูลประกาศ
# ---------------------------------------------------------------------------
class AnnounceModal(discord.ui.Modal, title="📢 สร้างประกาศ"):
    def __init__(self, color_value: int, ping_role: discord.Role | None):
        super().__init__()
        self.color_value = color_value
        self.ping_role = ping_role

    headline = discord.ui.TextInput(
        label="หัวข้อประกาศ",
        placeholder="เช่น  อัปเดตเซิร์ฟเวอร์ครั้งใหญ่!",
        max_length=256,
        required=True,
    )
    body = discord.ui.TextInput(
        label="เนื้อหา",
        style=discord.TextStyle.paragraph,
        placeholder="รายละเอียดประกาศ... รองรับ Markdown และอีโมจิ",
        max_length=4000,
        required=True,
    )
    image_url = discord.ui.TextInput(
        label="ลิงก์รูปภาพหลัก (ไม่บังคับ)",
        placeholder="https://...  (วางลิงก์รูปที่จะแสดงเต็มขนาด)",
        required=False,
    )
    thumbnail_url = discord.ui.TextInput(
        label="ลิงก์รูปย่อ/โลโก้มุมขวา (ไม่บังคับ)",
        placeholder="https://...  (รูปเล็กมุมขวาบน)",
        required=False,
    )
    footer = discord.ui.TextInput(
        label="ข้อความท้ายประกาศ (ไม่บังคับ)",
        placeholder="เช่น  ทีมงาน ProHub",
        max_length=2048,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # ตรวจ URL รูปก่อน
        img = str(self.image_url).strip()
        thumb = str(self.thumbnail_url).strip()

        if img and not is_valid_url(img):
            await interaction.response.send_message(
                "❌ ลิงก์รูปภาพหลักไม่ถูกต้อง ต้องขึ้นต้นด้วย http:// หรือ https://",
                ephemeral=True,
            )
            return
        if thumb and not is_valid_url(thumb):
            await interaction.response.send_message(
                "❌ ลิงก์รูปย่อไม่ถูกต้อง ต้องขึ้นต้นด้วย http:// หรือ https://",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=str(self.headline),
            description=str(self.body),
            color=self.color_value,
        )
        if img:
            embed.set_image(url=img)
        if thumb:
            embed.set_thumbnail(url=thumb)

        footer_text = str(self.footer).strip()
        if footer_text:
            embed.set_footer(
                text=footer_text,
                icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None,
            )

        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = discord.utils.utcnow()

        content = self.ping_role.mention if self.ping_role else None

        await interaction.channel.send(
            content=content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.response.send_message(
            "✅ ส่งประกาศเรียบร้อยแล้ว!", ephemeral=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.exception("Modal error", exc_info=error)
        msg = "❌ เกิดข้อผิดพลาดในการส่งประกาศ"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------
class AnnounceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # เริ่ม health check web server (port 8080) สำหรับ Fly.io
        from healthcheck import start_health_server

        await start_health_server()
        log.info("Health check server started on port %s", os.environ.get("PORT", "8080"))

        # ซิงค์ slash command กับ Discord
        synced = await self.tree.sync()
        log.info("Synced %d slash command(s)", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)
        log.info("Bot is ready in %d guild(s)", len(self.guilds))


bot = AnnounceBot()


# Choices สำหรับสีในเมนู
COLOR_CHOICES = [
    app_commands.Choice(name=name, value=name) for name in PRESET_COLORS
]


@bot.tree.command(name="announce", description="สร้างประกาศแบบสวยงาม ลงรูปได้ เลือกสีได้")
@app_commands.describe(
    สี="เลือกสีจากเมนู (ถ้าใส่ hex ในช่องถัดไปจะใช้ hex แทน)",
    hex="รหัสสีเอง เช่น #5865F2 (ไม่บังคับ — ทับค่าจากเมนู)",
    แท็กบทบาท="เลือกบทบาทที่จะแท็ก/ping พร้อมประกาศ (ไม่บังคับ)",
)
@app_commands.choices(สี=COLOR_CHOICES)
async def announce(
    interaction: discord.Interaction,
    สี: app_commands.Choice[str] | None = None,
    hex: str | None = None,
    แท็กบทบาท: discord.Role | None = None,
):
    # สิทธิ์: ต้องมีสิทธิ์จัดการข้อความ
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ คุณต้องมีสิทธิ์ **จัดการข้อความ (Manage Messages)** จึงจะใช้คำสั่งนี้ได้",
            ephemeral=True,
        )
        return

    # ลำดับความสำคัญ: hex > เมนูสี > ค่าเริ่มต้น
    color_value = None
    if hex:
        color_value = parse_color(hex)
        if color_value is None:
            await interaction.response.send_message(
                "❌ รหัส hex ไม่ถูกต้อง ตัวอย่างที่ถูก: `#5865F2`",
                ephemeral=True,
            )
            return
    elif สี:
        color_value = PRESET_COLORS.get(สี.value)

    if color_value is None:
        color_value = 0x5865F2  # ค่าเริ่มต้น = น้ำเงิน Discord

    await interaction.response.send_modal(
        AnnounceModal(color_value=color_value, ping_role=แท็กบทบาท)
    )


def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise SystemExit(
            "❌ ไม่พบ DISCORD_TOKEN — ตั้งค่า environment variable ก่อนรันบอท"
        )
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
