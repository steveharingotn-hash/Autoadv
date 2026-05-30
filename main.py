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
keys_data = {}
OWNER_ROLE_ID = 1506914867179819108   # ← CHANGE THIS TO YOUR OWNER ROLE ID

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
    print(f"✅ Bot is Online: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced!")
    except Exception as e:
        print(f"Sync error: {e}")

# ====================== KEY COMMANDS ======================
@bot.tree.command(name="generatekey", description="Generate a key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Owner role required!", ephemeral=True)

    key = f"REPLICA-{str(uuid.uuid4())[:8].upper()}"
    keys_data[key] = {"owner": interaction.user.id, "redeemed": False, "user_id": None}
    save_keys()

    await interaction.response.send_message(f"✅ **Key Generated!**\n```{key}```\nShare this with your customer.", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem a key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["redeemed"]:
        return await interaction.response.send_message("❌ Invalid or already used key!", ephemeral=True)

    keys_data[key]["redeemed"] = True
    keys_data[key]["user_id"] = interaction.user.id
    save_keys()

    await interaction.response.send_message("✅ **Key Redeemed!** You can now use `/panel`", ephemeral=True)

# ====================== PANEL ======================
@bot.tree.command(name="panel", description="Open Replica Control Panel")
async def panel(interaction: discord.Interaction):
    has_access = any(data.get("user_id") == interaction.user.id for data in keys_data.values())
    if not has_access:
        return await interaction.response.send_message("❌ Redeem a key first using `/redeem`", ephemeral=True)

    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Slot 1 selected. Use **Setup**", ephemeral=True)

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def addslot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Add Slot - Coming Soon", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def deleteslot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Delete Slot - Coming Soon", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Starting Advertising... (Basic)", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.secondary, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Setup coming soon...", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))