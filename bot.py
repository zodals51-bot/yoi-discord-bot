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

        guild = interaction.guild
        member = guild.get_member(interaction.user.id)

        if member is None:
            await interaction.followup.send("❌ 멤버 정보를 불러올 수 없습니다.")
            return

        # =========================
        # 닉네임 변경 (공통 적용)
        # =========================
        try:
            await member.edit(nick=f"{info['name']}/{info['class']}")
        except Exception as e:
            print("닉네임 변경 실패:", e)

        # =========================
        # 길드 체크 및 역할 분기
        # =========================
        roles_to_add = [info["class"]]  # 직업 역할은 누구나 지급
        
        # 실제 디스코드에 보낼 메시지 설정
        embed_title = "✅ 인증 완료"
        embed_color = 0x57F287  # 기본 초록색
        embed_description = f"**{info['name']}**님, 인증이 완료되었습니다."

        # 우리 길드가 맞는지 확인
        is_guild_member = info["guild"].strip() == config.GUILD_NAME.strip()

        if is_guild_member:
            # [길드원인 경우] 길드원 역할 추가
            roles_to_add.append(config.MEMBER_ROLE)
            print(f"📢 [길드원 확인] {info['name']} -> {config.GUILD_NAME}")
        else:
            # [외부인/지인인 경우] 외부인 역할 추가
            guest_role_name = getattr(config, "GUEST_ROLE", "외부인")
            roles_to_add.append(guest_role_name)
            
            # 외부인용 가시성 커스텀
            embed_title = "ℹ 외부인 인증 완료"
            embed_color = 0x3498DB  # 파란색
            current_guild = info['guild'] if info['guild'] else '없음'
            embed_description = f"**{info['name']}**님은 외부인(지인)으로 인증되었습니다.\n(조회된 길드: {current_guild})"
            print(f"📢 [외부인 확인] {info['name']} -> 소속 길드: {current_guild}")

        # =========================
        # 역할 실제 지급 처리
        # =========================
        for role_name in roles_to_add:
            role = discord.utils.get(guild.roles, name=role_name)

            if role:
                try:
                    await member.add_roles(role)
                    print(f"✔ 역할 지급: {role_name}")
                except Exception as e:
                    print(f"❌ 역할 지급 실패 ({role_name}):", e)
            else:
                print(f"❌ 서버에 역할 없음: {role_name}")

        # =========================
        # 인증대기 제거 (공통 적용)
        # =========================
        wait_role = discord.utils.get(guild.roles, name=config.WAIT_ROLE)

        if wait_role:
            try:
                await member.remove_roles(wait_role)
                print("✔ 인증대기 역할 제거 완료")
            except Exception as e:
                print("WAIT_ROLE 제거 실패:", e)

        # 결과 전달용 임베드 패널
        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="캐릭터명", value=info["name"], inline=True)
        embed.add_field(name="직업", value=info["class"], inline=True)
        
        await interaction.followup.send(embed=embed)


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
        title="로스트아크 길드 인증",
        description="아래 버튼을 눌러 인증하세요\n(지인분들도 동일하게 인증하시면 됩니다)",
        color=0x2B2D31
    )

    await ctx.send(embed=embed, view=VerifyView())


# =========================
# 실행
# =========================
bot.run(config.DISCORD_TOKEN)
