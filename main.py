import discord
from discord.ext import commands
import asyncio
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SLOTS_FILE = "slots.json"
slots_data = {}      # We'll use only Slot 1 for now
active_slot = None

class AdSlot:
    def __init__(self, token, channels, delay, message):
        self.token = token
        self.channels = [c.strip() for c in channels if c.strip()]
        self.delay = int(delay)
        self.message = message
        self.client = None
        self.task = None

    async def start(self):
        global active_slot
        active_slot = self
        self.client = discord.Client(intents=discord.Intents.default())

        @self.client.event
        async def on_ready():
            print(f"✅ Logged in as {self.client.user} | Advertising Active")

        try:
            await self.client.start(self.token)
            self.task = asyncio.create_task(self.advertise())
        except Exception as e:
            print(f"❌ Login Error: {e}")

    async def advertise(self):
        while True:
            for cid in self.channels:
                try:
                    channel = self.client.get_channel(int(cid))
                    if channel:
                        await channel.send(self.message)
                except:
                    pass
            await asyncio.sleep(self.delay)

    def stop(self):
        global active_slot
        if self.task:
            self.task.cancel()
        if self.client:
            asyncio.create_task(self.client.close())
        active_slot = None
        print("⛔ Stopped")

def load_slots():
    global slots_data
    if os.path.exists(SLOTS_FILE):
        try:
            with open(SLOTS_FILE) as f:
                slots_data = json.load(f)
        except:
            slots_data = {}

def save_slots():
    with open(SLOTS_FILE, "w") as f:
        json.dump(slots_data, f, indent=4)

load_slots()

# ====================== CONTROL PANEL ======================
class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("➕ Multiple slots coming soon...", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Delete coming soon...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "1" not in slots_data:
            return await interaction.response.send_message("❌ Please Setup Slot 1 first!", ephemeral=True)
        
        data = slots_data["1"]
        slot = AdSlot(data["token"], data["channels"], data["delay"], data["message"])
        await interaction.response.send_message("🚀 Starting Auto Advertiser...", ephemeral=True)
        asyncio.create_task(slot.start())

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if active_slot:
            active_slot.stop()
            await interaction.response.send_message("⛔ Advertising Stopped", ephemeral=True)
        else:
            await interaction.response.send_message("Not running currently.", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste your user token here", required=True)
    channels = discord.ui.TextInput(label="Target Channels *", placeholder="1471484118930952399, 1234567890", required=True)
    delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="10", required=True)
    message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="nigga gigga", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        slots_data["1"] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",")],
            "delay": int(self.delay.value),
            "message": self.message.value
        }
        save_slots()
        await interaction.response.send_message("✅ **Slot 1 Saved!**\nClick **Start** to begin advertising.", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica's Auto ADV Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔧 REPLICA CONTROL PANEL",
        description="Replica's Auto ADV",
        color=0x7289DA
    )
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is Online!")
    await bot.tree.sync()

# ================ RUN ================
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ DISCORD_TOKEN not found!")