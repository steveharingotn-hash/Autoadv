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
        self.client = discord.Client(intents=discord.Intents.default())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ Logged in")

        try:
            await self.client.start(self.token)
            self.task = asyncio.create_task(self.advertise())
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

# ====================== CONTROL PANEL ======================
class ReplicaControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Slot 1", style=discord.ButtonStyle.primary, row=0)
    async def slot1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal("1"))

    @discord.ui.button(label="+ Add Slot", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        next_slot = str(len(slots_data) + 1)
        if int(next_slot) > 8:
            return await interaction.response.send_message("❌ Maximum 8 slots reached!", ephemeral=True)
        
        slots_data[next_slot] = {"token": "", "channels": [], "delay": 10, "message": ""}
        save_slots()
        await interaction.response.send_message(f"✅ Slot {next_slot} Created! Click on it to setup.", ephemeral=True)

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
        await interaction.response.send_message("⛔ All slots stopped!", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=1)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Click on any Slot button to edit/setup", ephemeral=True)

class SetupModal(discord.ui.Modal):
    def __init__(self, slot_id):
        super().__init__(title=f"Setup Slot {slot_id}")
        self.slot_id = slot_id
        
        data = slots_data.get(slot_id, {})
        
        self.token = discord.ui.TextInput(
            label="Alt Token *", 
            placeholder="Paste your user token",
            default=data.get("token", ""),
            required=True
        )
        self.channels = discord.ui.TextInput(
            label="Target Channels *", 
            placeholder="1471484118930952399, 1234567890",
            default=", ".join(data.get("channels", [])),
            required=True
        )
        self.delay = discord.ui.TextInput(
            label="Delay (Sec) *", 
            placeholder="180",
            default=str(data.get("delay", 10)),
            required=True
        )
        self.message = discord.ui.TextInput(
            label="Ad Message *", 
            style=discord.TextStyle.paragraph,
            placeholder="Your ad message here",
            default=data.get("message", ""),
            required=True
        )
        
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            delay = int(self.delay.value)
            if delay < 5:
                return await interaction.response.send_message("❌ Delay must be at least 5 seconds!", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Delay must be a number!", ephemeral=True)

        slots_data[self.slot_id] = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": delay,
            "message": self.message.value.strip()
        }
        save_slots()
        await interaction.response.send_message(f"✅ **Slot {self.slot_id} Saved/Updated Successfully!**", ephemeral=True)

class DeleteModal(discord.ui.Modal, title="Delete Slot"):
    slot_id = discord.ui.TextInput(label="Slot Number to Delete", placeholder="2", required=True)

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