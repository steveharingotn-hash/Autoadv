import discord
import asyncio
import json
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

DATA_FILE = "slots.json"

def load_slots():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_slots(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

slots = load_slots()

async def send_ad(slot_id):
    slot = slots.get(str(slot_id))
    if not slot or not slot.get("running"):
        return
    for cid in slot.get("channels", []):
        try:
            channel = bot.get_channel(int(cid))
            if channel:
                await channel.send(slot["message"])
                print(f"[Slot {slot_id}] Sent to {cid}")
            await asyncio.sleep(1)
        except:
            pass

async def slot_loop(slot_id):
    while slots.get(str(slot_id), {}).get("running"):
        await send_ad(slot_id)
        await asyncio.sleep(slots[str(slot_id)]["delay"])

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is ready!")
    for sid in slots:
        if slots[sid].get("running"):
            asyncio.create_task(slot_loop(sid))

@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        return

    content = message.content.strip()
    if not content.startswith('/'):
        return

    parts = content.split()
    cmd = parts[0].lower()

    # /panel
    if cmd == "/panel":
        embed = discord.Embed(title="🔧 REPLICA AUTO ADV PANEL", color=0x00ff00)
        for sid, data in slots.items():
            status = "🟢 RUNNING" if data.get("running") else "🔴 STOPPED"
            embed.add_field(name=f"Slot {sid}", value=f"Delay: {data.get('delay')}s\nStatus: {status}", inline=False)
        await message.channel.send(embed=embed)

    # /addslot
    elif cmd == "/addslot":
        new_id = str(max([int(k) for k in slots.keys()] or [0]) + 1)
        slots[new_id] = {"channels": [], "delay": 10, "message": "nigga gigga", "running": False}
        save_slots(slots)
        await message.channel.send(f"✅ Slot {new_id} Created. Now setup it.")

    # /setup
    elif cmd == "/setup":
        try:
            # Format: /setup 1 TOKEN 1471484118930952399 10 nigga gigga
            slot_id = parts[1]
            token = parts[2]
            channels = [int(x) for x in parts[3].split(',')]
            delay = int(parts[4])
            message = " ".join(parts[5:])
            slots[slot_id] = {"channels": channels, "delay": delay, "message": message, "running": False}
            save_slots(slots)
            await message.channel.send(f"✅ Slot {slot_id} Saved!")
        except:
            await message.channel.send("❌ Format: `/setup <slot> <token> <channel_ids> <delay> <message>`")

    # /start
    elif cmd == "/start":
        slot_id = parts[1]
        if slot_id in slots:
            slots[slot_id]["running"] = True
            save_slots(slots)
            asyncio.create_task(slot_loop(slot_id))
            await message.channel.send(f"🟢 Slot {slot_id} Started Advertising!")
        else:
            await message.channel.send("❌ Slot not found")

    # /stop
    elif cmd == "/stop":
        slot_id = parts[1]
        if slot_id in slots:
            slots[slot_id]["running"] = False
            save_slots(slots)
            await message.channel.send(f"🔴 Slot {slot_id} Stopped!")

    # /deleteslot
    elif cmd == "/deleteslot":
        slot_id = parts[1]
        if slot_id in slots:
            slots[slot_id]["running"] = False
            del slots[slot_id]
            save_slots(slots)
            await message.channel.send(f"🗑️ Slot {slot_id} Deleted!")

# ====================== START ======================
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("Set DISCORD_TOKEN in Railway")