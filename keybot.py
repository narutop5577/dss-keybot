import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, hashlib
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", ""))
DB_FILE = "keys.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"keys": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_hard_key(hwid: str) -> str:
    clean = "".join(c for c in hwid.lower() if c.isalnum())
    half = clean[:8].ljust(8, "0")
    num1 = random.randint(1000, 9999)
    num2 = random.randint(1000, 9999)
    raw = f"{half}{num1}{num2}DSSMART2025NARUTO"
    checksum = hashlib.md5(raw.encode()).hexdigest()[:4]
    return f"dss{half}-{num1}-{num2}-{checksum}"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ KeyBot ready: {bot.user}")

@bot.tree.command(name="key", description="Generate key from HWID (Admin only)")
@app_commands.describe(hwid="User's HWID from APK")
async def key_cmd(interaction: discord.Interaction, hwid: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    if len(hwid) < 8:
        await interaction.response.send_message("❌ HWID too short.", ephemeral=True)
        return
    key = generate_hard_key(hwid)
    db = load_db()
    db["keys"][key] = {
        "hwid": hwid,
        "created_at": datetime.now().isoformat(),
        "active": True,
        "expiry": datetime.now().timestamp() + 30 * 86400
    }
    save_db(db)
    embed = discord.Embed(title="🔑 DSS MART KEY", color=0x00aaff, timestamp=datetime.now())
    embed.add_field(name="Key", value=f"```\n{key}\n```", inline=False)
    embed.add_field(name="HWID", value=f"`{hwid[:20]}...`", inline=True)
    embed.add_field(name="Valid", value="30 days", inline=True)
    embed.set_footer(text="DSS MART • NARUTO")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="revoke", description="Revoke a key (Admin)")
async def revoke(interaction: discord.Interaction, key: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    db = load_db()
    if key not in db["keys"]:
        await interaction.response.send_message("❌ Not found.", ephemeral=True)
        return
    db["keys"][key]["active"] = False
    save_db(db)
    await interaction.response.send_message(f"✅ Revoked: `{key}`", ephemeral=True)

@bot.tree.command(name="listkeys", description="List all keys (Admin)")
async def listkeys(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    db = load_db()
    if not db["keys"]:
        await interaction.response.send_message("No keys.", ephemeral=True)
        return
    active = sum(1 for k in db["keys"].values() if k["active"])
    embed = discord.Embed(title=f"📋 Keys: {len(db['keys'])}", description=f"✅ {active} | ❌ {len(db['keys'])-active}", color=0x00aaff)
    for k, v in list(db["keys"].items())[-10:]:
        s = "✅" if v["active"] else "❌"
        embed.add_field(name=f"{s} `{k}`", value=f"HWID: `{v['hwid'][:12]}...`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
