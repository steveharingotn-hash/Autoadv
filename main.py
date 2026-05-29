import discord
from discord.ext import commands
import asyncio
import os
import json
import uuid

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

KEYS_FILE = "keys.json"
keys_data = {}  # { "key": {"owner": user_id, "used": False, "active": False} }

OWNER_ROLE_ID = 123456789012345678  # ← CHANGE THIS to your Owner Role ID

def load_keys():
    global keys_data
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE) as f:
                keys_data = json.load(f)
        except:
            keys_data = {}

def save_keys():
    with open(KEYS_FILE, "w") as f:
        json.dump(keys_data, f, indent=4)

load_keys()

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")

@bot.tree.command(name="generatekey", description="Generate a key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Owner role required!", ephemeral=True)

    key = "REPLICA-" + str(uuid.uuid4())[:8].upper()
    keys_data[key] = {"owner": interaction.user.id, "used": False}
    save_keys()
    
    await interaction.response.send_message(f"✅ **Key Generated!**\n`{key}`\nShare this with your customer.", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem a key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["used"]:
        return await interaction.response.send_message("❌ Invalid or already used key!", ephemeral=True)

    keys_data[key]["used"] = True
    save_keys()
    await interaction.response.send_message("✅ **Key Redeemed Successfully!**\nYou can now use `/panel`", ephemeral=True)

@bot.tree.command(name="panel", description="Open Control Panel")
async def panel(interaction: discord.Interaction):
    # Simple check - anyone who redeemed a key can use
    await interaction.response.send_message("🔧 **REPLICA CONTROL PANEL**", view=ControlPanel(), ephemeral=True)

class ControlPanel(discord.ui.View):
    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️")
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Setup coming in next version...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Advertising Started (Basic Version)", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))