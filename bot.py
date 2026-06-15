import discord
from discord.ext import commands
import requests
import config
from flask import Flask
import threading
import os

# =========================
# 웹 서버 (Render 유지용)
# =========================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

# =========================
# 봇 설정
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# API 인증 처리
clean_key = str(config.LOSTARK_API_KEY).strip().replace(" ", "").replace("\n", "").replace("\r", "")
if clean_key.lower().startswith("bearer"): clean_key = clean_key[6:]
headers = {"accept": "application/json", "authorization": f"bearer {clean_key}"}

def get_character_info(character_name):
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{character_name}/profiles"
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return None
        data = r.json()
        return {"name": data["CharacterName"], "class": data["CharacterClassName"], 
                "item_level": data["ItemAvgLevel"], "guild": data.get("GuildName") or ""}
    except: return None

# =========================
# 인증 모달
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(label="캐릭터 이름", placeholder="캐릭터 이름 입력", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = get_character_info(self.character_name.value)
        if not info or info["guild"].strip() != config.GUILD_NAME.strip():
            await interaction.followup.send("❌ 인증 실패: 캐릭터 정보를 찾을 수 없거나 길드명이 일치하지 않습니다.")
            return

        guild = interaction.guild
        member = interaction.user

        # 1. 닉네임 변경
        try: await member.edit(nick=f"{info['name']}/{info['class']}")
        except Exception as e: print(f"⚠️ 닉네임 변경 실패: {e}")

        # 2. 역할 부여 및 디버깅
        # 서버의 모든 역할을 출력해서 이름 확인 (공백 체크)
        role_map = {r.name.strip(): r for r in guild.roles}
        
        target_roles = [info["class"], config.MEMBER_ROLE]
        for role_name in target_roles:
            role = role_map.get(role_name.strip())
            if role:
                await member.add_roles(role)
                print(f"✅ 역할 부여 완료: {role_name}")
            else:
                print(f"❌ [에러] '{role_name}' 역할을 서버에서 찾을 수 없습니다. 이름이 완벽히 일치하는지 확인하세요!")

        # 3. 인증대기 제거
        wait_role = role_map.get(config.WAIT_ROLE.strip())
        if wait_role: await member.remove_roles(wait_role)

        await interaction.followup.send("✅ 인증 완료!")

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

@bot.command()
async def 인증패널(ctx):
    await ctx.send(embed=discord.Embed(title="길드 인증", description="버튼 클릭"), view=VerifyView())

@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user}")
    bot.add_view(VerifyView()) # 봇 재시작해도 버튼 작동하게 설정

bot.run(config.DISCORD_TOKEN)
