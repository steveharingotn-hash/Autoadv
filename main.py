import discord
from discord.ext import commands
import asyncio
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SLOTS_FILE = "slots.json"
slots_data = {}      # Saved config
active_slots = {}    # Running slots

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
        self.client = discord.Client(intents=discord.Intents.default())
        active_slots[self.slot_id] = self

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in as {self.client.user} | Advertising...")

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
            with open(SLOTS_FILE) as f:
                slots_data = json.load(f)
        except:
            slots_data = {}

def save_slots():
    with open(SLOTS_FILE, "w") as f:
        json.dump(slots_data, f, indent=4)

load_slots()

# ==================== CONTROL PANEL ====================
class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot1_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(slots_data) >= 8:
            return await interaction.response.send_message("❌ Maximum 8 slots allowed!", ephemeral=True)
        await interaction.response.send_modal(AddSlotModal())

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeleteSlotModal())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 Starting Slot 1...", ephemeral=True)
        # You can expand this to select slot later

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Stopped Slot 1", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

class SetupModal(discord.ui.Modal, title="Setup Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number (1-8)", placeholder="1", required=True)
    alt_token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste user token", required=True)
    channels = discord.ui.TextInput(label="Channel IDs *", placeholder="1471484118930952399,1234567890", required=True)
    delay = discord.ui.TextInput(label="Delay (Seconds) *", placeholder="10", required=True)
    message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="Your advertisement here", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if not sid.isdigit() or int(sid) < 1 or int(sid) > 8:
            return await interaction.response.send_message("❌ Invalid Slot Number (1-8 only)", ephemeral=True)

        try:
            delay_sec = int(self.delay.value)
            if delay_sec < 5:
                return await interaction.response.send_message("❌ Delay must be at least 5 seconds!", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Delay must be a number!", ephemeral=True)

        slots_data[sid] = {
            "token": self.alt_token.value,
            "channels": [c.strip() for c in self.channels.value.split(",")],
            "delay": delay_sec,
            "message": self.message.value
        }
        save_slots()
        await interaction.response.send_message(f"✅ Slot {sid} Setup Successfully!", ephemeral=True)

class AddSlotModal(discord.ui.Modal, title="Add New Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number (1-8)", placeholder="2", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if sid in slots_data:
            await interaction.response.send_message("❌ Slot already exists!", ephemeral=True)
        elif int(sid) < 1 or int(sid) > 8:
            await interaction.response.send_message("❌ Slot must be 1-8!", ephemeral=True)
        else:
            slots_data[sid] = {"token": "", "channels": [], "delay": 10, "message": ""}
            save_slots()
            await interaction.response.send_message(f"➕ Slot {sid} Added! Now click Setup.", ephemeral=True)

class DeleteSlotModal(discord.ui.Modal, title="Delete Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number to Delete", placeholder="1", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sid = self.slot_id.value.strip()
        if sid in slots_data:
            slots_data.pop(sid)
            if sid in active_slots:
                active_slots[sid].stop()
            save_slots()
            await interaction.response.send_message(f"🗑️ Slot {sid} Deleted!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Slot not found!", ephemeral=True)

@bot.tree.command(name="panel", description="Open Replica's Auto ADV Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    
    for i in range(1, 9):
        data = slots_data.get(str(i))
        status = "🟢 Active" if str(i) in active_slots else ("⚙️ Configured" if data and data.get("token") else "⚪ Empty")
        embed.add_field(name=f"Slot {i}", value=status, inline=False)

    await interaction.response.send_message(embed=embed, view=ReplicaControlPanel())

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ DISCORD_TOKEN not found!")