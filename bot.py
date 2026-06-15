import discord
from discord.ext import commands
import requests
import config

# =========================
# 🔥 Render용 Flask (포트 열기)
# =========================
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()


# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# LOSTARK API 설정
# =========================
clean_key = str(config.LOSTARK_API_KEY).strip().replace(" ", "").replace("\n", "").replace("\r", "")

if clean_key.lower().startswith("bearer"):
    clean_key = clean_key[6:]

headers = {
    "accept": "application/json",
    "authorization": f"bearer {clean_key}"
}


def get_character_info(character_name):
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{character_name}/profiles"

    try:
        r = requests.get(url, headers=headers)
        print(f"📡 [로아 API 요청] {character_name} | 상태코드: {r.status_code}")

        if r.status_code != 200:
            print(f"❌ API 오류: {r.status_code}")
            return None

        data = r.json()

        if not data or "CharacterName" not in data:
            return None

        return {
            "name": data["CharacterName"],
            "class": data["CharacterClassName"],
            "item_level": data["ItemAvgLevel"],
            "guild": data.get("GuildName") or ""
        }

    except Exception as e:
        print(f"❌ API 통신 실패: {e}")
        return None


# =========================
# 인증 모달
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(
        label="캐릭터 이름",
        placeholder="캐릭터 이름 입력",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        info = get_character_info(self.character_name.value)

        if not info:
            await interaction.followup.send("❌ 캐릭터를 찾을 수 없습니다.")
            return

        user_guild = info["guild"].strip().lower()
        target_guild = config.GUILD_NAME.strip().lower()

        if user_guild != target_guild:
            await interaction.followup.send(
                f"❌ 길드 불일치 (조회: {info['guild']})"
            )
            return

        guild = interaction.guild
        member = interaction.user

        # 닉네임 변경
        try:
            nickname = f"{info['name']}/{info['class']}"
            await member.edit(nick=nickname)
        except:
            pass


        # 직업 역할
        class_role = discord.utils.get(guild.roles, name=info["class"])
        if class_role:
            await member.add_roles(class_role)


        # 길드원 역할
        member_role = discord.utils.get(guild.roles, name=config.MEMBER_ROLE)
        if member_role:
            await member.add_roles(member_role)


        # 인증대기 제거
        wait_role = discord.utils.get(guild.roles, name=config.WAIT_ROLE)
        if wait_role:
            await member.remove_roles(wait_role)


        embed = discord.Embed(title="✅ 인증 완료", color=0x57F287)
        embed.add_field(name="캐릭터", value=info["name"], inline=False)
        embed.add_field(name="직업", value=info["class"], inline=False)
        embed.add_field(name="아이템레벨", value=info["item_level"], inline=False)

        await interaction.followup.send(embed=embed)


# =========================
# 버튼 UI
# =========================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())


# =========================
# 인증패널 명령어
# =========================
@bot.command()
async def 인증패널(ctx):
    embed = discord.Embed(
        title="로스트아크 길드 인증",
        description="아래 버튼을 눌러 인증하세요",
        color=0x2B2D31
    )
    await ctx.send(embed=embed, view=VerifyView())


# =========================
# 이벤트
# =========================
@bot.event
async def on_ready():
    print("=================================")
    print(f"로그인 완료: {bot.user}")
    print("=================================")


@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=config.WAIT_ROLE)
    if role:
        await member.add_roles(role)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print(f"에러: {error}")


# =========================
# 실행
# =========================
bot.run(config.DISCORD_TOKEN)
