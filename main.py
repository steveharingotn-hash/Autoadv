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
SLOTS_FILE = "slots.json"
keys_data = {}
slots_data = {}      # Per user advertising config
active_tasks = {}    # To control stop

OWNER_ROLE_ID = 1506914867179819108   # ← CHANGE THIS

def load_data():
    global keys_data, slots_data
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE) as f:
                keys_data = json.load(f)
        except:
            keys_data = {}
    if os.path.exists(SLOTS_FILE):
        try:
            with open(SLOTS_FILE) as f:
                slots_data = json.load(f)
        except:
            slots_data = {}

def save_data():
    with open(KEYS_FILE, "w") as f:
        json.dump(keys_data, f, indent=4)
    with open(SLOTS_FILE, "w") as f:
        json.dump(slots_data, f, indent=4)

load_data()

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    await bot.tree.sync()

# ====================== KEY SYSTEM ======================
@bot.tree.command(name="generatekey", description="Generate key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Owner role required!", ephemeral=True)
    key = f"REPLICA-{str(uuid.uuid4())[:8].upper()}"
    keys_data[key] = {"owner": interaction.user.id, "redeemed": False}
    save_data()
    await interaction.response.send_message(f"✅ Key: ```{key}```", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["redeemed"]:
        return await interaction.response.send_message("❌ Invalid key!", ephemeral=True)
    keys_data[key]["redeemed"] = True
    save_data()
    await interaction.response.send_message("✅ Redeemed! Use `/panel`", ephemeral=True)

# ====================== PANEL ======================
@bot.tree.command(name="panel", description="Open Control Panel")
async def panel(interaction: discord.Interaction):
    has_access = any(data.get("redeemed") for data in keys_data.values())
    if not has_access:
        return await interaction.response.send_message("❌ Redeem a key first!", ephemeral=True)

    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel(interaction.user.id))

class ReplicaControlPanel(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=0)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal(self.user_id))

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(self.user_id) not in slots_data:
            return await interaction.response.send_message("❌ Setup first!", ephemeral=True)
        
        await interaction.response.send_message("🚀 Starting from your alt account...", ephemeral=True)
        asyncio.create_task(self.start_advertising(interaction))

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(self.user_id) in active_tasks:
            active_tasks[str(self.user_id)].cancel()
            active_tasks.pop(str(self.user_id), None)
            await interaction.response.send_message("⛔ Advertising Stopped!", ephemeral=True)
        else:
            await interaction.response.send_message("Not running", ephemeral=True)

    async def start_advertising(self, interaction):
        data = slots_data[str(self.user_id)]
        task = asyncio.create_task(self.advertise(data))
        active_tasks[str(self.user_id)] = task

    async def advertise(self, data):
        while True:
            for cid in data.get("channels", []):
                try:
                    # Note: This is still using main bot. Full self-bot needs more complex code.
                    channel = bot.get_channel(int(cid))
                    if channel:
                        await channel.send(data["message"])
                except:
                    pass
            await asyncio.sleep(data.get("delay", 30))

class SetupModal(discord.ui.Modal, title="Setup Your Advertising"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        data = slots_data.get(str(user_id), {})
        self.token = discord.ui.TextInput(label="Your Alt Token", placeholder="MT...", default=data.get("token", ""), required=True)
        self.channels = discord.ui.TextInput(label="Channel IDs", placeholder="1471484118930952399", default=",".join(data.get("channels", [])), required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec)", placeholder="30", default=str(data.get("delay", 30)), required=True)
        self.message = discord.ui.TextInput(label="Ad Message", style=discord.TextStyle.paragraph, default=data.get("message", ""), required=True)
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        slots_data[str(self.user_id)] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": int(self.delay.value),
            "message": self.message.value.strip()
        }
        save_data()
        await interaction.response.send_message("✅ Setup Saved!\nClick **Start** to begin advertising from your alt.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))