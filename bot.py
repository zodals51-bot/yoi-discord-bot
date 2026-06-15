import discord
from discord.ext import commands
import requests
import config

# =========================
# INTENTS (디스코드 권한 설정)
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# LOSTARK API (로아 연동 및 공백 자동 청소)
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
        print(f"📡 [로아 API 요청] 닉네임: {character_name} | 상태코드: {r.status_code}")
        
        if r.status_code == 401:
            print("❌ [로아 에러] API 키 인증 실패 (401).")
            return None
        elif r.status_code == 403:
            print("❌ [로아 에러] API 키 만료 또는 권한 없음 (403).")
            return None
        elif r.status_code == 404:
            print("❌ [로아 에러] 존재하지 않는 캐릭터명입니다 (404).")
            return None
        elif r.status_code != 200:
            print(f"❌ [로아 에러] 기타 오류 발생 (상태코드: {r.status_code})")
            return None

        data = r.json()
        if not data or "CharacterName" not in data:
            print("❌ [로아 에러] 캐릭터 프로필 데이터를 찾을 수 없습니다.")
            return None

        return {
            "name": data["CharacterName"],
            "class": data["CharacterClassName"],
            "item_level": data["ItemAvgLevel"],
            "guild": data.get("GuildName") or ""
        }
    except Exception as e:
        print(f"❌ [로아 통신 자체 실패] 인터넷 연결이나 코드 에러: {e}")

    return None


# =========================
# 인증 모달 UI
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
            await interaction.followup.send("❌ 캐릭터를 찾을 수 없습니다. (로아 공식 홈페이지 점검 중이거나 이름 오타일 수 있습니다.)")
            return

        # 길드명 체크
        user_guild = info["guild"].strip().lower()
        target_guild = config.GUILD_NAME.strip().lower()

        if user_guild != target_guild:
            await interaction.followup.send(f"❌ 길드원이 아닙니다. (조회된 길드: '{info['guild']}' / 설정된 길드: '{config.GUILD_NAME}')")
            return

        guild = interaction.guild
        member = interaction.user

        # 1. 닉네임 변경 (⭐ 캐릭터명/직업명 형태로 수정 완료)
        try:
            nickname = f"{info['name']}/{info['class']}"
            await member.edit(nick=nickname)
            print(f"✅ [닉네임 변경 성공] {member.name} -> {nickname}")
        except Exception as e:
            print(f"⚠️ [닉네임 변경 실패] 봇의 서열이 유저보다 낮거나 권한이 부족합니다: {e}")

        # 2. 직업 역할 부여
        class_role = discord.utils.get(guild.roles, name=info["class"])
        if class_role:
            await member.add_roles(class_role)
            print(f"✅ [직업 역할 부여] {info['class']} 역할 지급 완료")
        else:
            print(f"⚠️ [역할 미지급] 서버에 '{info['class']}' 이름과 일치하는 역할이 없습니다.")

        # 3. 길드원 역할 부여
        member_role = discord.utils.get(guild.roles, name=config.MEMBER_ROLE)
        if member_role:
            await member.add_roles(member_role)
            print(f"✅ [길드원 역할 부여] {config.MEMBER_ROLE} 역할 지급 완료")

        # 4. 인증대기 역할 회수
        wait_role = discord.utils.get(guild.roles, name=config.WAIT_ROLE)
        if wait_role:
            await member.remove_roles(wait_role)
            print(f"✅ [인증대기 역할 회수] {config.WAIT_ROLE} 역할 제거 완료")

        # 결과 Embed 전송
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
# 인증 패널 명령어
# =========================
@bot.command()
async def 인증패널(ctx):
    print(f"▶️ [명령어 감지] {ctx.author.name}님이 !인증패널 명령어를 실행했습니다.")
    
    embed = discord.Embed(
        title="로스트아크 길드 인증",
        description="아래 버튼을 눌러 인증을 진행하세요",
        color=0x2B2D31
    )

    try:
        await ctx.send(embed=embed, view=VerifyView())
        print("✅ [성공] 인증패널 메시지를 전송했습니다.")
    except Exception as e:
        print(f"❌ [전송 실패] 채널에 메시지나 임베드를 보낼 권한이 없습니다: {e}")


# =========================
# 봇 이벤트 시스템
# =========================
@bot.event
async def on_ready():
    print(f"=================================")
    print(f"로그인 완료 : {bot.user}")
    
    key = getattr(config, "LOSTARK_API_KEY", "")
    clean_k = str(key).strip().replace(" ", "").replace("\n", "").replace("\r", "")
    print(f"🔑 [API 키 상태 진단 결과]")
    print(f"  - 원본 글자 수: {len(key)}자")
    print(f"  - 공백 제거 후 글자 수: {len(clean_k)}자")
    print(f"  - 연동 대상 길드 설정값: {config.GUILD_NAME}")
    print(f"=================================")


@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=config.WAIT_ROLE)
    if role:
        await member.add_roles(role)
        print(f"📥 [신규 유저 입장] {member.name}님에게 '{config.WAIT_ROLE}' 역할을 부여했습니다.")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"👀 [메시지 수신] 채널: #{message.channel.name} | 작성자: {message.author.name} | 내용: {message.content}")
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print(f"🚨 [디스코드 명령어 에러] {error}")


# =========================
# 실행
# =========================
bot.run(config.DISCORD_TOKEN)

import os

token = os.getenv("TOKEN")
bot.run(token)