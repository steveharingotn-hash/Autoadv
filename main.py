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
        print(f"[Slot {self.slot_id}] Trying to login with token...")
        active_slots[self.slot_id] = self
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print(f"[Slot {self.slot_id}] ✅ LOGGED IN SUCCESSFULLY AS: {self.client.user}")
            print(f"🚀 Advertising Started - Message: '{self.message[:50]}...' | Delay: {self.delay}s")
            self.task = asyncio.create_task(self.advertise())

        try:
            await self.client.start(self.token, bot=False)
        except Exception as e:
            print(f"[Slot {self.slot_id}] ❌ FAILED TO LOGIN: {e}")

    async def advertise(self):
        while True:
            for cid in self.channels:
                try:
                    channel = self.client.get_channel(int(cid))
                    if channel:
                        await channel.send(self.message)
                        print(f"[Slot {self.slot_id}] ✅ Sent to {cid}")
                    else:
                        print(f"[Slot {self.slot_id}] Channel {cid} not found")
                except Exception as e:
                    print(f"[Slot {self.slot_id}] Error: {e}")
            await asyncio.sleep(self.delay)

    def stop(self):
        if self.task:
            self.task.cancel()
        if self.client:
            asyncio.create_task(self.client.close())
        active_slots.pop(self.slot_id, None)

# Rest of the code (Panel + Setup) remains same as last version
# ... (I kept it short to save space)

# [Paste the full ReplicaControlPanel, SetupModal, etc. from my previous message here]
# Or just replace the AdSlot class with this new one in your current code.