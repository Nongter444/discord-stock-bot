import discord
from discord.ext import tasks, commands
import yfinance as yf
from datetime import datetime

# ================= โซนตั้งค่า (Config) =================
with open("token_sniper.txt", "r") as file:
    TOKEN = file.read().strip()
CHANNEL_ID = 1470731818201518130 # เป็นตัวเลขล้วนๆ ไม่มีเครื่องหมายคำพูด

# 🎯 โซนเล็งเป้าหมาย! (ใส่เพิ่มได้ไม่อั้น พิมพ์ตัวย่อหุ้น : ราคาเป้าหมาย)
TARGETS = {
    'FIG': 21.00,
    'ADBE': 300.00,
    'NVDA': 170.00,
    'QUBT': 9.50,
    'IONQ': 30.00
}

VOLUME_SPIKE = 2000000   # เกณฑ์ Volume เทขายเดือด
# ====================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ถังเก็บชื่อหุ้นที่บอทเตือนไปแล้ว (จะได้ไม่สแปมแชทรัวๆ)
alerted_tickers = set()

@bot.event
async def on_ready():
    print(f'✅ สไนเปอร์ {bot.user.name} เข้าประจำสถานีรบแล้ว!')
    print(f'🎯 กำลังเฝ้าเป้าหมาย: {", ".join(TARGETS.keys())}')
    check_price_loop.start()

@tasks.loop(minutes=5)
async def check_price_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    # ลูปเช็คหุ้นทีละตัวจากในรายการ TARGETS
    for ticker, target_price in TARGETS.items():
        # ถ้าตัวไหนเตือนไปแล้ว ให้ข้ามไปเช็คตัวอื่นต่อเลย
        if ticker in alerted_tickers:
            continue 

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d") 
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔎 เล็ง {ticker}: ราคา ${current_price:.2f} | เป้า: ${target_price:.2f}")

                # ลั่นไก! ถ้าราคาลงมาแตะเป้า
                if current_price <= target_price:
                    embed = discord.Embed(
                        title=f"🚨 สัญญาณสไนเปอร์: {ticker} เข้าโซนสังหาร!!",
                        description=f"**{ticker}** ร่วงลงมาแตะเป้าหมายแล้วครับเฮีย! โหลดกระสุนด่วน!",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="📉 ราคาปัจจุบัน", value=f"**${current_price:.2f}**", inline=True)
                    embed.add_field(name="🎯 ราคาเป้าหมาย", value=f"${target_price:.2f}", inline=True)
                    embed.add_field(name="📊 Volume", value=f"{current_volume:,}", inline=False)
                    
                    if current_volume >= VOLUME_SPIKE:
                        embed.set_footer(text="⚠️ คำเตือน: Volume เทขายเดือดมาก! เลือดสาดเต็มกระดาน!")
                    else:
                        embed.set_footer(text="✅ Volume ปกติ ทะยอยเก็บของเซลล์ได้เลย")

                    # เอา @everyone ออกแล้ว เตือนเงียบๆ แบบหล่อๆ
                    await channel.send(f"🔫 เฮีย! ตื่นมาเก็บของเซลล์ {ticker}!", embed=embed)
                    
                    # จำไว้ว่าเตือนตัวนี้ไปแล้ว จะได้ไม่ส่งซ้ำ
                    alerted_tickers.add(ticker)

        except Exception as e:
            print(f"⚠️ ดึงข้อมูล {ticker} ล้มเหลว: {e}")

# คำสั่งล้างความจำบอท ให้มันกลับมาเฝ้าหุ้นที่เคยเตือนไปแล้วใหม่
@bot.command()
async def reset(ctx):
    alerted_tickers.clear()
    await ctx.send("🔄 รีเซ็ตเรดาร์สไนเปอร์แล้ว! กลับมาเฝ้าเป้าหมายทุกตัวใหม่ครับเฮีย 😎")

bot.run(TOKEN)