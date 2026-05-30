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
slots_data = {}
OWNER_ROLE_ID = 1506914867179819108   # ← CHANGE TO YOUR OWNER ROLE ID

active_slots = {}

class AdSlot:
    def __init__(self, slot_id, token, channels, delay, message):
        self.slot_id = slot_id
        self.token = token.strip()
        self.channels = [c.strip() for c in str(channels).split(",") if c.strip()]
        self.delay = max(30, int(delay))
        self.message = message
        self.client = None
        self.task = None

    async def start(self):
        active_slots[self.slot_id] = self
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in as {self.client.user}")
            self.task = asyncio.create_task(self.advertise())

        try:
            await self.client.start(self.token)
        except Exception as e:
            print(f"[Slot {self.slot_id}] Login Failed: {e}")

    async def advertise(self):
        while True:
            for cid in self.channels:
                try:
                    channel = self.client.get_channel(int(cid))
                    if channel:
                        await channel.send(self.message)
                        print(f"[Slot {self.slot_id}] Sent to {cid}")
                except:
                    pass
            await asyncio.sleep(self.delay)

    def stop(self):
        if self.task:
            self.task.cancel()
        if self.client:
            asyncio.create_task(self.client.close())
        active_slots.pop(self.slot_id, None)

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
    print(f"✅ Panel Bot Online: {bot.user}")
    await bot.tree.sync()

# Key System
@bot.tree.command(name="generatekey", description="Generate key (Owner only)")
async def generatekey(interaction: discord.Interaction):
    if not any(role.id == OWNER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Owner role required!", ephemeral=True)
    key = f"REPLICA-{str(uuid.uuid4())[:8].upper()}"
    keys_data[key] = {"owner": interaction.user.id, "redeemed": False, "user_id": None}
    save_data()
    await interaction.response.send_message(f"✅ Key: ```{key}```", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem key")
async def redeem(interaction: discord.Interaction, key: str):
    if key not in keys_data or keys_data[key]["redeemed"]:
        return await interaction.response.send_message("❌ Invalid key!", ephemeral=True)
    keys_data[key]["redeemed"] = True
    keys_data[key]["user_id"] = interaction.user.id
    save_data()
    await interaction.response.send_message("✅ Redeemed! Use `/panel`", ephemeral=True)

# Panel
@bot.tree.command(name="panel", description="Open Control Panel")
async def panel(interaction: discord.Interaction):
    has_access = any(d.get("user_id") == interaction.user.id for d in keys_data.values())
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
        if "1" not in slots_data or not slots_data["1"].get("token"):
            return await interaction.response.send_message("❌ Setup Slot 1 first!", ephemeral=True)
        
        data = slots_data["1"]
        slot = AdSlot("1", data["token"], data["channels"], data["delay"], data["message"])
        await interaction.response.send_message("🚀 Starting from your alt account...", ephemeral=True)
        asyncio.create_task(slot.start())

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "1" in active_slots:
            active_slots["1"].stop()
            await interaction.response.send_message("⛔ Stopped", ephemeral=True)
        else:
            await interaction.response.send_message("Not running", ephemeral=True)

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    def __init__(self):
        super().__init__()
        data = slots_data.get("1", {})
        self.token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste your user token", default=data.get("token", ""), required=True)
        self.channels = discord.ui.TextInput(label="Channel IDs *", placeholder="1471484118930952399", default=",".join(data.get("channels", [])), required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="30", default=str(data.get("delay", 30)), required=True)
        self.message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="Your ad here", default=data.get("message", ""), required=True)
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        slots_data["1"] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": int(self.delay.value),
            "message": self.message.value.strip()
        }
        save_data()
        await interaction.response.send_message("✅ Saved! Click **Start** to advertise from your alt account.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))