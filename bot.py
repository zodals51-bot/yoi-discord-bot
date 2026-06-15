import discord
from discord.ext import commands
import requests
import config
import traceback

# =========================
# 봇 설정
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# API 설정
clean_key = str(config.LOSTARK_API_KEY).strip().replace(" ", "").replace("bearer", "").strip()
headers = {"accept": "application/json", "authorization": f"bearer {clean_key}"}

def get_character_info(character_name):
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{character_name}/profiles"
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return None
        data = r.json()
        return {"name": data["CharacterName"], "class": data["CharacterClassName"], "guild": data.get("GuildName") or ""}
    except: return None

# =========================
# UI 및 로직
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(label="캐릭터 이름", placeholder="캐릭터 이름 입력", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = get_character_info(self.character_name.value)
        
        if not info or info["guild"].strip() != config.GUILD_NAME.strip():
            await interaction.followup.send("❌ 캐릭터 정보 불일치 또는 길드명 불일치")
            return

        guild = interaction.guild
        member = interaction.user

        # 1. 닉네임
        try: await member.edit(nick=f"{info['name']}/{info['class']}")
        except: pass

        # 2. 역할 부여 (이름 비교를 더 유연하게)
        roles_to_add = [info["class"], config.MEMBER_ROLE]
        for role_name in roles_to_add:
            role = discord.utils.find(lambda r: r.name.strip() == role_name.strip(), guild.roles)
            if role:
                await member.add_roles(role)
            else:
                print(f"❌ '{role_name}' 역할을 서버에서 찾을 수 없습니다!")

        # 3. 인증대기 제거
        wait_role = discord.utils.find(lambda r: r.name.strip() == config.WAIT_ROLE.strip(), guild.roles)
        if wait_role: await member.remove_roles(wait_role)

        await interaction.followup.send("✅ 인증 완료!")

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

@bot.event
async def on_ready():
    bot.add_view(VerifyView()) # 버튼 영구 등록
    print(f"✅ 로그인 완료: {bot.user}")

@bot.command()
async def 인증패널(ctx):
    await ctx.send(embed=discord.Embed(title="길드 인증", description="버튼을 눌러 인증하세요"), view=VerifyView())

bot.run(config.DISCORD_TOKEN)
