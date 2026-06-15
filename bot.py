import discord
from discord.ext import commands
import requests
import config

# =========================
# 봇 설정
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# 로스트아크 API
# =========================
clean_key = str(config.LOSTARK_API_KEY).strip().replace(" ", "").replace("bearer", "").strip()

headers = {
    "accept": "application/json",
    "authorization": f"bearer {clean_key}"
}


def get_character_info(character_name):
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{character_name}/profiles"

    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return None

        data = r.json()

        return {
            "name": data["CharacterName"],
            "class": data["CharacterClassName"],
            "guild": data.get("GuildName") or ""
        }

    except Exception as e:
        print("API 오류:", e)
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
            await interaction.followup.send("❌ 캐릭터 정보를 찾을 수 없습니다.")
            return

        # 길드 체크
        if info["guild"].strip() != config.GUILD_NAME.strip():
            await interaction.followup.send("❌ 길드가 일치하지 않습니다.")
            return

        guild = interaction.guild

        # =========================
        # 🔥 핵심 수정 (member 객체)
        # =========================
        member = guild.get_member(interaction.user.id)

        if member is None:
            await interaction.followup.send("❌ 멤버 정보를 불러올 수 없습니다.")
            return

        # =========================
        # 닉네임 변경
        # =========================
        try:
            await member.edit(nick=f"{info['name']}/{info['class']}")
        except Exception as e:
            print("닉네임 변경 실패:", e)

        # =========================
        # 역할 지급
        # =========================
        roles_to_add = [info["class"], config.MEMBER_ROLE]

        for role_name in roles_to_add:
            role = discord.utils.get(guild.roles, name=role_name)

            if role:
                try:
                    await member.add_roles(role)
                    print(f"✔ 역할 지급: {role_name}")
                except Exception as e:
                    print(f"❌ 역할 지급 실패 ({role_name}):", e)
            else:
                print(f"❌ 역할 없음: {role_name}")

        # =========================
        # 인증대기 제거
        # =========================
        wait_role = discord.utils.get(guild.roles, name=config.WAIT_ROLE)

        if wait_role:
            try:
                await member.remove_roles(wait_role)
            except Exception as e:
                print("WAIT_ROLE 제거 실패:", e)

        await interaction.followup.send("✅ 인증 완료!")


# =========================
# 버튼 UI
# =========================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="인증하기",
        style=discord.ButtonStyle.green,
        custom_id="verify_btn"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())


# =========================
# 봇 시작
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    print(f"✅ 로그인 완료: {bot.user}")


# =========================
# 인증 패널
# =========================
@bot.command()
async def 인증패널(ctx):
    embed = discord.Embed(
        title="길드 인증",
        description="버튼을 눌러 인증하세요",
        color=0x2B2D31
    )

    await ctx.send(embed=embed, view=VerifyView())


# =========================
# 실행
# =========================
bot.run(config.DISCORD_TOKEN)
