import discord
from discord.ext import tasks, commands
import yfinance as yf
from datetime import datetime
import pytz
import mplfinance as mpf # พระเอกของเรา
import io
import asyncio # เพิ่มตัวนี้มาช่วยให้ทำงานลื่นขึ้น
# --- ตั้งค่า Bot ---
with open("token_check.txt", "r") as file:
    BOT_TOKEN = file.read().strip()
CHANNEL_ID = 1470731818201518130  # เลขห้อง Discord ที่จะให้บอทพ่น (คลิกขวาที่ห้อง > Copy ID)
# รายชื่อหุ้นของคุณ (รวมจากในรูป + ที่ขอเพิ่ม)
STOCKS = [
    "FIG",       # Figma (ในพอร์ต)
    "NFLX",      # Netflix (ในพอร์ต)
    "ADBE",      # Adobe (ในพอร์ต)
    "NVDA",      # Nvidia (ในพอร์ต)
    "QUBT",      # Quantum Computing (ในพอร์ต)
    "MARA",      # Marathon Digital (ในพอร์ต)
    "MSFT",      # Microsoft (ในพอร์ต)
    "IONQ",      # IonQ (ในพอร์ต)
    "DUOL",      # Duolingo (ในพอร์ต)
    "V",         # Visa (ในพอร์ต)
    "GC=F",      # ทองคำ (Gold Futures) **
    "BTC-USD",   # Bitcoin
    "AMZN",      # Amazon
    "GOOGL"      # Google
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# --- ฟังก์ชั่นสร้างกราฟ (เหมือนเดิม) ---
def create_candle_chart(symbol):
    try:
        data = yf.Ticker(symbol).history(period="5d", interval="30m", prepost=True)
        if data.empty: return None

        mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000', edge='inherit', wick='inherit', volume='in')
        s  = mpf.make_mpf_style(marketcolors=mc, base_mpf_style='nightclouds', gridstyle=':')
        
        buffer = io.BytesIO()
        mpf.plot(
            data, type='candle', style=s, title=f'\n{symbol} (Extended Hours)',
            ylabel='Price ($)', volume=True,
            savefig=dict(fname=buffer, dpi=100, bbox_inches='tight', pad_inches=0.1)
        )
        buffer.seek(0)
        return buffer
    except: return None

# --- ฟังก์ชั่นส่งรายงาน (แก้ใหม่: เพิ่มใบสรุปตอนท้าย) ---
async def send_report(target, title_prefix="Snapshot"):
    summary_list = [] # เตรียมกระดาษเปล่าไว้จดสรุป

    # วนลูปส่งทีละตัว
    for symbol in STOCKS:
        try:
            stock = yf.Ticker(symbol)
            todays_data = stock.history(period="1d", interval="1m", prepost=True)
            
            if not todays_data.empty:
                price = todays_data['Close'].iloc[-1]
                open_price = todays_data['Open'].iloc[0]
                change = ((price - open_price) / open_price) * 100
                emoji = "🟢" if change >= 0 else "🔴"
                
                # 1. ส่งกราฟรายตัวออกไปก่อน (เหมือนเดิม)
                chart_buffer = create_candle_chart(symbol)
                if chart_buffer:
                    file = discord.File(chart_buffer, filename=f"{symbol}.png")
                    embed = discord.Embed(
                        title=f"{emoji} {title_prefix}: {symbol}", 
                        description=f"ราคาล่าสุด: **${price:,.2f}** ({change:+.2f}%)", 
                        color=0x00ff00 if change >= 0 else 0xff0000
                    )
                    embed.set_image(url=f"attachment://{symbol}.png")
                    
                    if isinstance(target, discord.Interaction):
                        await target.followup.send(embed=embed, file=file)
                    else:
                        await target.send(embed=embed, file=file)
                
                # 2. จดข้อมูลลงใบสรุป (เก็บไว้ก่อน)
                summary_list.append(f"{emoji} **{symbol}**: ${price:,.2f} (`{change:+.2f}%`)")
                
                # พักหายใจนิดนึง กัน Discord บล็อกเพราะส่งเร็วเกิน
                await asyncio.sleep(1) 
                
        except Exception as e:
            print(f"Error sending {symbol}: {e}")

    # 3. ส่งใบสรุปรวมยอด (The Grand Summary)
    if summary_list:
        summary_text = "\n".join(summary_list)
        summary_embed = discord.Embed(
            title=f"📊 สรุปภาพรวมตลาด ({title_prefix})",
            description=summary_text,
            color=0xFFD700 # สีทอง ดูแพง
        )
        summary_embed.set_footer(text=f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        if isinstance(target, discord.Interaction):
            await target.followup.send(embed=summary_embed)
        else:
            await target.send(embed=summary_embed)

# --- เมนูเลือกหุ้น ---
class StockSelect(discord.ui.Select):
    def __init__(self):
        # Discord จำกัด Dropdown ให้มีได้แค่ 25 ตัว (ของเรามี 14 ยังรอด)
        options = [discord.SelectOption(label=s, emoji="📈") for s in STOCKS]
        super().__init__(placeholder="🔍 เลือกหุ้นที่อยากดูกราฟ...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        symbol = self.values[0]
        # เรียกใช้ logic เดียวกับการส่งกราฟรายตัว
        chart_buffer = create_candle_chart(symbol)
        if chart_buffer:
            file = discord.File(chart_buffer, filename=f"{symbol}.png")
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d", interval="1m", prepost=True)
            price = data['Close'].iloc[-1]
            embed = discord.Embed(title=f"📊 กราฟ {symbol}", description=f"ราคา: **${price:,.2f}**", color=0x00ff00)
            embed.set_image(url=f"attachment://{symbol}.png")
            await interaction.followup.send(embed=embed, file=file)

class MenuButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StockSelect())

@bot.command()
async def stock(ctx):
    await ctx.send("👇 **เลือกหุ้นเพื่อดูกราฟ (รวม Pre/Post Market)** 👇", view=MenuButton())

# --- ระบบตั้งเวลา ---
@tasks.loop(minutes=1)
async def scheduled_task():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")
    weekday = now.weekday() # 0=จันทร์, 1=อังคาร, ... 5=เสาร์, 6=อาทิตย์
    
    # ==========================================
    # ลอจิกหยุดทำงานเสาร์-อาทิตย์ (ฉบับเซียนหุ้นไทย)
    # ==========================================
    # 1. วันเสาร์: ทำงานแค่ตอนเช้า (ตี 4 ตลาดปิดวันศุกร์ และ 8 โมงเช้า) นอกนั้นหยุด
    if weekday == 5 and current_time not in ["04:00", "08:00"]:
        return
    # 2. วันอาทิตย์: หยุดทำงานทั้งวัน
    if weekday == 6:
        return
    # 3. เช้าวันจันทร์: (ตี 4 และ 8 โมง) ตลาดเพิ่งผ่านวันหยุดมา ให้ข้ามไปเลย
    if weekday == 0 and current_time in ["04:00", "08:00"]:
        return
    # ==========================================
    
    report_title = None
    target_times = ["08:00", "16:00", "21:30", "04:00", "22:00"]

    if current_time in target_times:
        if current_time == "16:00": report_title = "Pre-market"
        elif current_time == "21:30": report_title = "Market Open"
        elif current_time == "04:00": report_title = "Market Close"
        elif current_time == "08:00": report_title = "Overnight"
        elif current_time == "22:00": report_title = "Update" # เผื่อรอบ 4 ทุ่ม
        
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            print(f"Time match: {current_time} (Day: {weekday})")
            await channel.send(f"📢 **แจ้งเตือนรอบ: {report_title}** เริ่มส่งข้อมูล...")
            await send_report(channel, title_prefix=report_title)

@bot.event
async def on_ready():
    print(f'Bot Ready: {bot.user}')
    scheduled_task.start()

bot.run(BOT_TOKEN)