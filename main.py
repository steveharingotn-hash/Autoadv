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
OWNER_ROLE_ID = 1506914867179819108   # ← CHANGE THIS
slots_data = {}   # For advertising config

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
        print("✅ Commands synced!")
    except:
        pass

# ====================== KEY SYSTEM ======================
@bot.tree.command(name="generatekey", description="Generate redeem key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Owner role required!", ephemeral=True)
    
    key = f"REPLICA-{str(uuid.uuid4())[:8].upper()}"
    keys_data[key] = {"owner": interaction.user.id, "redeemed": False, "user_id": None}
    save_keys()
    await interaction.response.send_message(f"✅ Key Generated!\n```{key}```", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem a key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["redeemed"]:
        return await interaction.response.send_message("❌ Invalid key!", ephemeral=True)
    
    keys_data[key]["redeemed"] = True
    keys_data[key]["user_id"] = interaction.user.id
    save_keys()
    await interaction.response.send_message("✅ Key Redeemed! Use `/panel`", ephemeral=True)

# ====================== PANEL + ADVERTISING ======================
@bot.tree.command(name="panel", description="Open Replica Control Panel")
async def panel(interaction: discord.Interaction):
    has_access = any(data.get("user_id") == interaction.user.id for data in keys_data.values())
    if not has_access:
        return await interaction.response.send_message("❌ Redeem a key first!", ephemeral=True)

    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=0)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "1" not in slots_data or not slots_data["1"].get("message"):
            return await interaction.response.send_message("❌ Setup first!", ephemeral=True)
        
        await interaction.response.send_message("🚀 Advertising Started!", ephemeral=True)
        asyncio.create_task(self.advertise(interaction))

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped!", ephemeral=True)

    async def advertise(self, interaction):
        while True:
            try:
                for cid in slots_data["1"].get("channels", []):
                    channel = bot.get_channel(int(cid))
                    if channel:
                        await channel.send(slots_data["1"]["message"])
            except:
                pass
            await asyncio.sleep(slots_data["1"].get("delay", 30))

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    def __init__(self):
        super().__init__()
        data = slots_data.get("1", {})
        self.channels = discord.ui.TextInput(label="Channel IDs", placeholder="1471484118930952399", default=",".join(data.get("channels", [])), required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec)", placeholder="30", default=str(data.get("delay", 30)), required=True)
        self.message = discord.ui.TextInput(label="Ad Message", style=discord.TextStyle.paragraph, placeholder="Your advertisement", default=data.get("message", ""), required=True)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        slots_data["1"] = {
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": int(self.delay.value),
            "message": self.message.value.strip()
        }
        await interaction.response.send_message("✅ Slot 1 Configured!\nClick **Start** to begin advertising.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))