import discord
from discord.ext import commands
import asyncio
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SLOTS_FILE = "slots.json"
slots_data = {}  # { "1": {...}, "2": {...} }
active_slots = {}  # {slot_id: AdSlot instance}

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
        if self.slot_id in active_slots:
            return
        active_slots[self.slot_id] = self
        self.client = discord.Client(intents=discord.Intents.default())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in as {self.client.user}")
            self.task = asyncio.create_task(self.advertise())

        try:
            await self.client.start(self.token)
        except Exception as e:
            print(f"Slot {self.slot_id} Error: {e}")

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
            with open(SLOTS_FILE, "r") as f:
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
    async def slot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddSlotModal())

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ Delete feature coming soon...", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Starting Slot 1...", ephemeral=True)
        # Expand later for multiple slots

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped Slot 1", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

class SetupModal(discord.ui.Modal, title="Setup Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number (1-8)", placeholder="1", required=True)
    token = discord.ui.TextInput(label="Alt Token", placeholder="Paste user token", required=True)
    channels = discord.ui.TextInput(label="Target Channel IDs", placeholder="1471484118930952399, 9876543210", required=True)
    delay = discord.ui.TextInput(label="Delay (seconds)", placeholder="10", required=True)
    message = discord.ui.TextInput(label="Ad Message", style=discord.TextStyle.paragraph, placeholder="nigga gigga", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if not sid.isdigit() or int(sid) < 1 or int(sid) > 8:
            return await interaction.response.send_message("❌ Slot must be 1-8!", ephemeral=True)

        slots_data[sid] = {
            "token": self.token.value,
            "channels": self.channels.value.split(","),
            "delay": int(self.delay.value),
            "message": self.message.value
        }
        save_slots()

        await interaction.response.send_message(f"✅ Slot {sid} Saved!", ephemeral=True)

class AddSlotModal(discord.ui.Modal, title="Add New Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number (1-8)", placeholder="2", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if sid in slots_data:
            await interaction.response.send_message("❌ Slot already exists!", ephemeral=True)
        elif int(sid) < 1 or int(sid) > 8:
            await interaction.response.send_message("❌ Slot 1-8 only!", ephemeral=True)
        else:
            slots_data[sid] = {"token": "", "channels": [], "delay": 10, "message": ""}
            save_slots()
            await interaction.response.send_message(f"➕ Slot {sid} Created! Use Setup to configure.", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica's Auto ADV Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔧 REPLICA CONTROL PANEL",
        description="Replica's Auto ADV",
        color=0x7289DA
    )
    
    for sid in range(1, 9):
        data = slots_data.get(str(sid))
        status = "🟢 Running" if str(sid) in active_slots else ("⚙️ Configured" if data else "⚪ Empty")
        embed.add_field(
            name=f"Slot {sid}",
            value=status,
            inline=True
        )

    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is ready!")
    await bot.tree.sync()

# Run Bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Set DISCORD_TOKEN in Railway!")
