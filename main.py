import discord
from discord.ext import commands
import asyncio
import os
import json

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
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ LOGGED IN AS: {self.client.user}")
            print(f"[Slot {self.slot_id}] 🚀 Starting Advertising | Delay: {self.delay}s")
            self.task = asyncio.create_task(self.advertise())

        try:
            await self.client.start(self.token, bot=False)   # ← Important for User Token
        except Exception as e:
            print(f"[Slot {self.slot_id}] ❌ LOGIN FAILED: {e}")

    async def advertise(self):
        while True:
            for cid in self.channels:
                try:
                    channel = self.client.get_channel(int(cid))
                    if channel:
                        await channel.send(self.message)
                        print(f"[Slot {self.slot_id}] ✅ Sent to {cid}")
                    else:
                        print(f"[Slot {self.slot_id}] ⚠️ Channel {cid} not found")
                except Exception as e:
                    print(f"[Slot {self.slot_id}] Error in {cid}: {e}")
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
    async def slot1(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = "✅ Configured" if slots_data.get("1", {}).get("token") else "⚪ Empty"
        await interaction.response.send_message(f"**Slot 1:** {status}\nUse Setup to configure.", ephemeral=True)

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Multiple slots coming soon...", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Coming soon...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "1" not in slots_data or not slots_data["1"].get("token"):
            return await interaction.response.send_message("❌ Setup Slot 1 first!", ephemeral=True)
        if "1" in active_slots:
            return await interaction.response.send_message("⚠️ Already Running!", ephemeral=True)

        data = slots_data["1"]
        slot = AdSlot("1", data["token"], data["channels"], data["delay"], data["message"])
        await interaction.response.send_message("🚀 Starting Advertising...", ephemeral=True)
        asyncio.create_task(slot.start())

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "1" in active_slots:
            active_slots["1"].stop()
            await interaction.response.send_message("⛔ Stopped!", ephemeral=True)
        else:
            await interaction.response.send_message("Not running.", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    def __init__(self):
        super().__init__()
        data = slots_data.get("1", {})
        self.token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste user token", default=data.get("token", ""), required=True)
        self.channels = discord.ui.TextInput(label="Target Channels *", placeholder="1471484118930952399,1234567890", default=", ".join(data.get("channels", [])), required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="180", default=str(data.get("delay", 10)), required=True)
        self.message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="nigga gigga", default=data.get("message", ""), required=True)
        
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            delay = int(self.delay.value)
            if delay < 5:
                return await interaction.response.send_message("❌ Minimum delay 5 seconds!", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Delay must be a number!", ephemeral=True)

        slots_data["1"] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": delay,
            "message": self.message.value.strip()
        }
        save_slots()
        await interaction.response.send_message("✅ Slot 1 Saved! Now click **Start**.", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

@bot.event
async def on_ready():
    print(f"✅ Control Panel Bot Online")
    await bot.tree.sync()

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ DISCORD_TOKEN not set!")