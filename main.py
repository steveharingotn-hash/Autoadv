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
        self.delay = int(delay)          # ← Delay is properly stored
        self.message = message
        self.client = None
        self.task = None

    async def start(self):
        active_slots[self.slot_id] = self
        self.client = discord.Client(intents=discord.Intents.default())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in | Delay: {self.delay} seconds")

        try:
            await self.client.start(self.token)
            self.task = asyncio.create_task(self.advertise())
        except Exception as e:
            print(f"Slot {self.slot_id} Login Failed: {e}")

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
            await asyncio.sleep(self.delay)   # ← Delay is used here

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
        await interaction.response.send_modal(SetupModal("1"))

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        next_slot = str(len(slots_data) + 1)
        if int(next_slot) > 8:
            return await interaction.response.send_message("❌ Max 8 slots!", ephemeral=True)
        
        slots_data[next_slot] = {"token": "", "channels": [], "delay": 10, "message": ""}
        save_slots()
        await interaction.response.send_message(f"✅ Slot {next_slot} Created!", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeleteModal())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        count = 0
        for sid, data in slots_data.items():
            if data.get("token"):
                slot = AdSlot(sid, data["token"], data["channels"], data["delay"], data["message"])
                asyncio.create_task(slot.start())
                count += 1
        await interaction.response.send_message(f"🚀 Started {count} slot(s)!", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        for slot in list(active_slots.values()):
            slot.stop()
        await interaction.response.send_message("⛔ All slots stopped.", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Click any **Slot X** button to setup.", ephemeral=True)

class SetupModal(discord.ui.Modal):
    def __init__(self, slot_id):
        super().__init__(title=f"Setup Slot {slot_id}")
        self.slot_id = slot_id
        self.token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste user token", required=True)
        self.channels = discord.ui.TextInput(label="Channel IDs *", placeholder="1471484118930952399,1234567890", required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="10", required=True)
        self.message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="nigga gigga", required=True)
        
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        slots_data[self.slot_id] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",")],
            "delay": int(self.delay.value),
            "message": self.message.value.strip()
        }
        save_slots()
        await interaction.response.send_message(f"✅ Slot {self.slot_id} Saved Successfully!", ephemeral=True)

class DeleteModal(discord.ui.Modal, title="Delete Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number (1-8)", placeholder="2", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if sid in slots_data:
            if sid in active_slots:
                active_slots[sid].stop()
            del slots_data[sid]
            save_slots()
            await interaction.response.send_message(f"🗑️ Slot {sid} Deleted!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Slot not found!", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica's Auto ADV Panel")
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