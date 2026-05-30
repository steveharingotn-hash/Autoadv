import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ui import View, Button

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

DATA_FILE = "slots.json"

def load_slots():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_slots(slots):
    with open(DATA_FILE, 'w') as f:
        json.dump(slots, f, indent=4)

slots = load_slots()

async def send_ad(slot_id):
    slot = slots.get(str(slot_id))
    if not slot or not slot.get("running"):
        return
    try:
        for cid in slot.get("channels", []):
            channel = bot.get_channel(int(cid))
            if channel:
                await channel.send(slot["message"])
                print(f"[Slot {slot_id}] Sent → {cid} | {datetime.now().strftime('%H:%M:%S')}")
            await asyncio.sleep(1.2)
    except Exception as e:
        print(f"[Slot {slot_id}] Error: {e}")

async def slot_loop(slot_id):
    while True:
        slot = slots.get(str(slot_id))
        if not slot or not slot.get("running"):
            break
        await send_ad(slot_id)
        await asyncio.sleep(slot.get("delay", 10))

class ControlPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Add Slot", style=discord.ButtonStyle.green)
    async def add_slot(self, interaction: discord.Interaction, button: Button):
        new_id = str(max([int(k) for k in slots.keys()] or [0]) + 1)
        slots[new_id] = {"token": "", "channels": [], "delay": 10, "message": "nigga gigga", "running": False}
        save_slots(slots)
        await interaction.response.send_message(f"➕ Slot **{new_id}** Created!", ephemeral=True)

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.blurple)
    async def setup_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("**Setup any slot**\nType: `/setup <slot_id> | token | ch1,ch2 | delay | message`", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Type: `/start <slot_id>`", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Type: `/stop <slot_id>`", ephemeral=True)

    @discord.ui.button(label="Delete Slot", style=discord.ButtonStyle.gray)
    async def delete_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Type: `/deleteslot <slot_id>`", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} | Auto Advertiser Ready")
    for sid in list(slots.keys()):
        if slots[sid].get("running"):
            asyncio.create_task(slot_loop(int(sid)))

@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        return

    content = message.content.strip()

    if content == "/panel":
        embed = discord.Embed(title="🔧 REPLICA'S AUTO ADV CONTROL PANEL", color=0x7289da)
        embed.description = "Use buttons below"
        for sid, data in slots.items():
            status = "🟢 Running" if data.get("running") else "🔴 Stopped"
            embed.add_field(name=f"Slot {sid}", value=f"Delay: {data.get('delay')}s | Status: {status}", inline=True)
        view = ControlPanel()
        await message.channel.send(embed=embed, view=view)

    elif content.startswith("/setup"):
        try:
            full = content[7:].strip()
            parts = [p.strip() for p in full.split('|')]
            if len(parts) < 5:
                return await message.channel.send("❌ Format: `/setup slot_id | token | ch1,ch2 | delay | message`")
            slot_id = parts[0]
            token = parts[1]
            channels = [int(x.strip()) for x in parts[2].split(',') if x.strip()]
            delay = int(parts[3])
            msg = parts[4]
            
            slots[slot_id] = {
                "token": token,
                "channels": channels,
                "delay": delay,
                "message": msg,
                "running": False
            }
            save_slots(slots)
            await message.channel.send(f"✅ **Slot {slot_id}** Saved!")
        except:
            await message.channel.send("❌ Invalid format")

    elif content.startswith("/start"):
        slot_id = content[7:].strip()
        slot = slots.get(slot_id)
        if slot and not slot.get("running"):
            slot["running"] = True
            save_slots(slots)
            asyncio.create_task(slot_loop(int(slot_id)))
            await message.channel.send(f"🟢 **Slot {slot_id}** Started Advertising!")
        else:
            await message.channel.send("❌ Slot not found or already running")

    elif content.startswith("/stop"):
        slot_id = content[6:].strip()
        slot = slots.get(slot_id)
        if slot and slot.get("running"):
            slot["running"] = False
            save_slots(slots)
            await message.channel.send(f"🔴 **Slot {slot_id}** Stopped!")
        else:
            await message.channel.send("❌ Not running")

    elif content.startswith("/deleteslot"):
        slot_id = content[12:].strip()
        if slot_id in slots:
            if slots[slot_id].get("running"):
                slots[slot_id]["running"] = False
            del slots[slot_id]
            save_slots(slots)
            await message.channel.send(f"🗑️ **Slot {slot_id}** Deleted!")

    elif content == "/addslot":
        new_id = str(max([int(k) for k in slots.keys()] or [0]) + 1)
        slots[new_id] = {"token": "", "channels": [], "delay": 10, "message": "nigga gigga", "running": False}
        save_slots(slots)
        await message.channel.send(f"➕ **Slot {new_id}** Created!")

# Run
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Set DISCORD_TOKEN in Railway Variables")
    else:
        bot.run(token)