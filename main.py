import discord
from discord.ext import commands
import asyncio
import os
import json
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SLOTS_FILE = "slots.json"
slots_data = {}
active_slots = {}

class AdSlot:
    def __init__(self, slot_id, token, channels, delay, message):
        self.slot_id = slot_id
        self.token = token
        self.channels = [c.strip() for c in channels if c.strip()]
        self.delay = int(delay)
        self.message = message
        self.client = None
        self.task = None

    async def start(self):
        active_slots[self.slot_id] = self
        self.client = discord.Client(intents=discord.Intents.default())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in as {self.client.user}")

        try:
            await self.client.start(self.token)
            self.task = asyncio.create_task(self.advertise())
        except Exception as e:
            print(f"Slot {self.slot_id} Failed: {e}")

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
        if self.task:
            self.task.cancel()
        if self.client:
            asyncio.create_task(self.client.close())
        active_slots.pop(self.slot_id, None)

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

class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        next_slot = str(len(slots_data) + 1)
        if int(next_slot) > 8:
            return await interaction.response.send_message("❌ Max 8 slots!", ephemeral=True)
        slots_data[next_slot] = {"token": "", "channels": [], "delay": 10, "message": ""}
        save_slots()
        await interaction.response.send_message(f"✅ Slot {next_slot} Created!", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Delete feature coming soon...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Starting...", ephemeral=True)
        for sid, data in slots_data.items():
            if data.get("token"):
                slot = AdSlot(sid, data["token"], data["channels"], data["delay"], data["message"])
                asyncio.create_task(slot.start())

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        for slot in list(active_slots.values()):
            slot.stop()
        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste your full user token", required=True)
    channels = discord.ui.TextInput(label="Target Channels *", placeholder="1471484118930952399, 1234567890", required=True)
    delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="180", required=True)
    message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="Your ad here", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # === Strict Validation ===
        token = self.token.value.strip()
        if len(token) < 50:
            return await interaction.response.send_message("❌ Invalid Token! Paste full user token.", ephemeral=True)

        # Channel IDs validation
        channel_list = [x.strip() for x in self.channels.value.split(",") if x.strip()]
        if not channel_list:
            return await interaction.response.send_message("❌ Please enter at least one Channel ID.", ephemeral=True)
        for cid in channel_list:
            if not cid.isdigit():
                return await interaction.response.send_message("❌ Channel IDs must be numbers only!", ephemeral=True)

        # Delay validation
        try:
            delay_sec = int(self.delay.value)
            if delay_sec < 5:
                return await interaction.response.send_message("❌ Delay must be at least 5 seconds.", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Delay must be a number!", ephemeral=True)

        # Message validation
        if len(self.message.value.strip()) < 3:
            return await interaction.response.send_message("❌ Ad Message is too short!", ephemeral=True)

        # Save if all good
        slots_data["1"] = {
            "token": token,
            "channels": channel_list,
            "delay": delay_sec,
            "message": self.message.value.strip()
        }
        save_slots()

        await interaction.response.send_message("✅ **Slot 1 Saved Successfully!**\nClick **Start** to begin advertising.", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica's Auto ADV Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

@bot.event
async def on_ready():
    print(f"✅ Bot is Online: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ DISCORD_TOKEN not set!")