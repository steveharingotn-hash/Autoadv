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
keys_data = {}        # {"KEY123": {"owner": user_id, "redeemed": False, "user_id": None}}
OWNER_ROLE_ID = 1506914867179819108   # ← CHANGE THIS TO YOUR SERVER'S OWNER ROLE ID

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

# ====================== KEY SYSTEM ======================
@bot.tree.command(name="generatekey", description="Generate redeem key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You need Owner role!", ephemeral=True)

    key = f"REPLICA-{str(uuid.uuid4())[:8].upper()}"
    keys_data[key] = {"owner": interaction.user.id, "redeemed": False, "user_id": None}
    save_keys()

    await interaction.response.send_message(f"✅ **Key Generated!**\n`{key}`\nGive this to your customer.", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem a key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["redeemed"]:
        return await interaction.response.send_message("❌ Invalid or already used key!", ephemeral=True)

    keys_data[key]["redeemed"] = True
    keys_data[key]["user_id"] = interaction.user.id
    save_keys()

    await interaction.response.send_message("✅ **Key Redeemed Successfully!**\nYou can now use `/panel`", ephemeral=True)

# ====================== CONTROL PANEL ======================
@bot.tree.command(name="panel", description="Open Replica Control Panel")
async def panel(interaction: discord.Interaction):
    # Check if user has redeemed any key
    has_access = any(data.get("user_id") == interaction.user.id for data in keys_data.values())
    
    if not has_access:
        return await interaction.response.send_message("❌ You need to redeem a key first!", ephemeral=True)

    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use **Setup** button below", ephemeral=True)

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def addslot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Add Slot coming soon...", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def deleteslot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Delete coming soon...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Advertising Started (Basic)", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.secondary, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Setup Modal coming in next update...", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))