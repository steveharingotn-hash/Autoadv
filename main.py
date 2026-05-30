import discord
from discord.ext import commands
import asyncio
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

slots_data = {}
active_slot = None

class AdSlot:
    def __init__(self, token, channels, delay, message):
        self.token = token.strip()
        self.channels = [c.strip() for c in str(channels).split(",") if c.strip()]
        self.delay = max(30, int(delay))
        self.message = message
        self.client = None
        self.task = None

    async def start(self):
        global active_slot
        active_slot = self
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print(f"✅ SELF-BOT LOGGED IN AS: {self.client.user}")
            print(f"🚀 Advertising every {self.delay} seconds")
            self.task = asyncio.create_task(self.advertise())

        try:
            await self.client.start(self.token, bot=False)
        except Exception as e:
            print(f"❌ LOGIN FAILED: {e}")
            print("Token blocked or invalid.")

    async def advertise(self):
        while True:
            for cid in self.channels:
                try:
                    channel = self.client.get_channel(int(cid))
                    if channel:
                        await channel.send(self.message)
                        print(f"✅ Sent to {cid}")
                except Exception as e:
                    print(f"Send error: {e}")
            await asyncio.sleep(self.delay)

    def stop(self):
        if self.task:
            self.task.cancel()
        if self.client:
            asyncio.create_task(self.client.close())

@bot.tree.command(name="panel", description="Open Control Panel")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🔧 REPLICA CONTROL PANEL", description="Replica's Auto ADV", color=0x7289DA)
    await interaction.response.send_message(embed=embed, view=ControlPanel())

class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.gray, emoji="⚙️", row=0)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not slots_data.get("token"):
            return await interaction.response.send_message("❌ Do Setup first!", ephemeral=True)
        
        slot = AdSlot(slots_data["token"], slots_data["channels"], slots_data["delay"], slots_data["message"])
        await interaction.response.send_message("🚀 Trying to start self-bot...", ephemeral=True)
        asyncio.create_task(slot.start())

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⭕", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global active_slot
        if active_slot:
            active_slot.stop()
            await interaction.response.send_message("⛔ Stopped", ephemeral=True)
        else:
            await interaction.response.send_message("Not running", ephemeral=True)

class SetupModal(discord.ui.Modal, title="Setup Slot 1"):
    def __init__(self):
        super().__init__()
        data = slots_data
        self.token = discord.ui.TextInput(label="Alt Token *", placeholder="Paste fresh user token", default=data.get("token", ""), required=True)
        self.channels = discord.ui.TextInput(label="Channel IDs *", placeholder="1471484118930952399", default=",".join(data.get("channels", [])), required=True)
        self.delay = discord.ui.TextInput(label="Delay (Sec) *", placeholder="30", default=str(data.get("delay", 30)), required=True)
        self.message = discord.ui.TextInput(label="Ad Message *", style=discord.TextStyle.paragraph, placeholder="nigga gigga", default=data.get("message", ""), required=True)
        self.add_item(self.token)
        self.add_item(self.channels)
        self.add_item(self.delay)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        global slots_data
        slots_data = {
            "token": self.token.value.strip(),
            "channels": [x.strip() for x in self.channels.value.split(",") if x.strip()],
            "delay": int(self.delay.value),
            "message": self.message.value.strip()
        }
        await interaction.response.send_message("✅ Saved! Click **Start**", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))