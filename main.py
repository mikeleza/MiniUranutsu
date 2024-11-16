import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import os

from server import server_on

# ตั้งค่าบอท
intents = discord.Intents.default()
intents.messages = True  # เปิดใช้งานการอ่านข้อความเพื่อฟังการตอบกลับ
bot = commands.Bot(command_prefix="!", intents=intents)

# กำหนด user_id ของผู้ใช้ที่ต้องการส่งข้อความไป
USER_ID = os.getenv('user_id_first')  # แทนด้วย ID ของผู้ใช้ที่ต้องการส่ง DM

# เวลาที่ต้องการเตือนให้กินยา พร้อมข้อความที่ต้องการส่ง
remind_times = [
    {"hour": 11, "minute": 00, "message": "กินยาแล้วหรือยังคะ"},
    {"hour": 12, "minute": 30, "message": "กินยาแล้วหรือยังเอ่ย"},
    {"hour": 13, "minute": 00, "message": "กินยาได้แล้วมั้งคะ"}
]

# สถานะการเตือน
remind_status = {
    "needs_reminder": True,
    "waiting_for_response": False,  # ใช้ตัวแปรนี้เพื่อเช็คว่าบอทกำลังรอคำตอบจากผู้ใช้หรือไม่
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    # print_time.start()  # เริ่มการพิมพ์เวลาปัจจุบันทุก 1 วินาที
    remind_user.start()  # เริ่มการเตือนผู้ใช้ตามเวลาที่กำหนด
    reset_daily_status.start()  # เริ่มการรีเซ็ตสถานะทุก ๆ เที่ยงคืน

@tasks.loop(seconds=1)  # พิมพ์เวลาทุก 1 วินาทีใน console
async def print_time():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"Current time: {current_time}")

@tasks.loop(seconds=60)  # ตรวจสอบเวลาทุก ๆ นาที
async def remind_user():
    now = datetime.now()
    for time in remind_times:
        # ตรวจสอบว่าเป็นเวลาที่กำหนดและยังต้องการเตือน
        time_key = (time["hour"], time["minute"])
        if now.hour == time["hour"] and now.minute == time["minute"] and remind_status["needs_reminder"]:
            remind_status["waiting_for_response"] = True  # บอทเริ่มรอคำตอบจากผู้ใช้
            user = await bot.fetch_user(USER_ID)
            if user:
                try:
                    await user.send(time["message"])  # ส่งข้อความเตือนให้กินยา
                    print(f"ส่งข้อความเตือนผู้ใช้ที่ {time['hour']}:{time['minute']} - {time['message']}")
                except discord.Forbidden:
                    print("ไม่สามารถส่งข้อความไปยัง DM ได้")
            break

@tasks.loop(hours=24)  # รีเซ็ตสถานะทุก ๆ 24 ชั่วโมง หรือ เที่ยงคืน
async def reset_daily_status():
    now = datetime.now()
    # คำนวณเวลาที่เหลือจนถึงเที่ยงคืน
    target_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    wait_time = (target_time - now).total_seconds()
    
    # รอจนถึงเที่ยงคืน
    await asyncio.sleep(wait_time)
    
    # รีเซ็ตสถานะ
    remind_status["needs_reminder"] = True  # เริ่มการเตือนใหม่
    remind_status["waiting_for_response"] = False  # หยุดรอคำตอบจากผู้ใช้
    print("สถานะรีเซ็ตแล้วในวันนี้")

@bot.event
async def on_message(message):
    # ตรวจสอบว่าข้อความมาจากผู้ใช้ที่กำหนดและเป็น DM
    if message.author.id == USER_ID and isinstance(message.channel, discord.DMChannel):
        # เช็คว่าเราอยู่ในสถานะรอคำตอบจากผู้ใช้หรือไม่
        if remind_status["waiting_for_response"]:
            # ตรวจสอบคำตอบ
            if "กิน" in message.content:
                if "เดี๋ยว" in message.content:  # ถ้ามีคำว่า "เดี๋ยว" มาด้วย
                    # ถือว่าเป็นคำตอบ "ยังไม่กิน"
                    await message.channel.send("ยังไม่กินใช่มั้ยคะ? เดี๋ยวจะมาเตือนใหม่นะคะ")
                    remind_status["waiting_for_response"] = False  # หยุดรอคำตอบ
                    print("ผู้ใช้ตอบว่า 'กิน' แต่มี 'เดี๋ยว' ถือว่าเป็นยังไม่กิน")
                else:
                    # ถ้าผู้ใช้ตอบว่า "กิน" โดยไม่มีคำว่า "เดี๋ยว"
                    await message.channel.send("เก่งมากค่ะ!")  # ส่งข้อความกลับไป
                    remind_status["needs_reminder"] = False  # หยุดการเตือนในครั้งถัดไป
                    remind_status["waiting_for_response"] = False  # หยุดรอคำตอบ
                    
                    # ส่งข้อความไปยัง user ID อื่น ๆ
                    other_user_id = os.getenv('user_id_second')  # ใส่ user ID ของผู้ที่ต้องการส่งข้อความไป
                    other_user = await bot.fetch_user(other_user_id)
                    if other_user:
                        try:
                            await other_user.send("น้องณัฐกินยาแล้วนะคะ")  # ส่งข้อความให้ผู้ใช้คนอื่น
                            print(f"ข้อความแจ้งไปยังผู้ใช้ ว่ากินยาไปแล้ว")
                        except discord.Forbidden:
                            print("ไม่สามารถส่งข้อความไปยัง DM ของผู้ใช้อื่นได้")
                    
                    print("ผู้ใช้ตอบว่า 'กิน' หยุดการเตือนในเวลาที่เหลือของวัน")
            elif "ไม่" in message.content or "ยัง" in message.content:
                # ถ้าผู้ใช้ตอบว่า "ไม่" หรือ "ยัง"
                await message.channel.send("กินยาด้วยนะคะ เดี๋ยวจะมาเตือนใหม่นะ")  # ส่งข้อความเตือนให้
                print("ผู้ใช้ตอบว่า 'ไม่' หรือ 'ยัง' จะเตือนต่อไปตามเวลาที่กำหนด")
                remind_status["waiting_for_response"] = False  # หยุดรอคำตอบ
            else:
                # ถ้าผู้ใช้ตอบอะไรที่ไม่ใช่คำตอบที่คาดหวัง
                await message.channel.send("กรุณาตอบว่า 'กิน' หรือ 'ไม่' เพื่อให้บอททราบค่ะ")
        else:
            # ถ้าบอทไม่ได้รอคำตอบก็จะไม่ทำอะไร
            pass

    await bot.process_commands(message)

server_on()
# รันบอท (ใส่ TOKEN ของบอทของคุณในนี้)
bot.run(os.getenv('DISCORD_TOKEN'))
