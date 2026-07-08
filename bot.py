import discord
from discord.ext import commands
import requests
import config
import re  # 큐브 입력을 파싱하기 위한 정규표현식 라이브러리

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
# 인증 버튼 UI
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
# 🔥 [신규 추가] 큐브 계산 모달 창
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 2인 큐브 동기화 계산기"):
    my_tickets = discord.ui.TextInput(
        label="내 티켓 정보",
        placeholder="예시: 4해금 3, 3해금 8, 2해금 4",
        style=discord.TextStyle.long,
        required=True
    )
    partner_tickets = discord.ui.TextInput(
        label="상대방 티켓 정보",
        placeholder="예시: 4해금 2, 3해금 9, 2해금 7",
        style=discord.TextStyle.long,
        required=True
    )

    # 문자열에서 해금단계와 개수를 뽑아내는 헬퍼 함수
    def parse_tickets(self, text):
        result = {4: 0, 3: 0, 2: 0, 1: 0}
        # "4해금 3", "3단계 2", "2해금2" 같은 패턴에서 숫자 쌍 매칭
        matches = re.findall(r'([1-4])[^\d]*(\d+)', text)
        for stage, count in matches:
            result[int(stage)] = int(count)
        return result

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        # 유저들의 입력값 파싱
        me = self.parse_tickets(self.my_tickets.value)
        partner = self.parse_tickets(self.partner_tickets.value)

        embed = discord.Embed(title="📊 큐브 2인 최적 소모 동선", color=0x9B59B6)
        embed.description = "두 분이 함께 파티를 맺고 아래 가이드대로 입장권을 소모해 보세요!\n─"

        has_data = False

        # 4해금부터 1해금까지 연산
        for stage in [4, 3, 2, 1]:
            me_count = me[stage]
            partner_count = partner[stage]

            if me_count == 0 and partner_count == 0:
                continue

            stage_text = ""

            # 1. 공통 3배(3장 빼기) 소모 계산
            me_triples = me_count // 3
            partner_triples = partner_count // 3
            common_triples = min(me_triples, partner_triples)

            if common_triples > 0:
                stage_text += f"**🔥 [3배 빼기] 함께 {common_triples}회 진행**\n"
                me_count -= common_triples * 3
                partner_count -= common_triples * 3

            # 2. 남은 짜투리 공통 1배(1장 녹이기) 소모 계산
            common_singles = min(me_count, partner_count)
            if common_singles > 0:
                stage_text += f"**💧 [1배 녹이기] 함께 {common_singles}회 진행**\n"
                me_count -= common_singles
                partner_count -= common_singles

            # 3. 남은 잔여 티켓 알림
            if me_count > 0:
                stage_text += f"⚠️ 내 티켓이 **{me_count}장** 남습니다. (개별 소모 권장)\n"
            if partner_count > 0:
                stage_text += f"⚠️ 상대방 티켓이 **{partner_count}장** 남습니다. (개별 소모 권장)\n"

            if stage_text:
                embed.add_field(name=f"▶️ {stage}해금 에브니 큐브", value=stage_text, inline=False)
                has_data = True

        if not has_data:
            await interaction.followup.send("❌ 입력 양식이 잘못되었거나 계산할 티켓 정보가 없습니다.")
            return

        await interaction.followup.send(embed=embed)


# =========================
# 🔥 [신규 추가] 큐브 버튼 UI
# =========================
class CubeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="큐브 정산하기",
        style=discord.ButtonStyle.blurple,
        custom_id="cube_calc_btn"
    )
    async def cube_calc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CubeCalculatorModal())


# =========================
# 봇 시작
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(CubeView())  # 큐브 뷰도 봇이 켜질 때 영속(Persistent)뷰로 등록
    print(f"✅ 로그인 완료: {bot.user}")


# =========================
# 명령어 - 인증 패널
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
# 🔥 [신규 추가] 명령어 - 큐브 패널
# =========================
@bot.command()
async def 큐브계산기(ctx):
    embed = discord.Embed(
        title="🎲 큐브 2인 동기화 매칭",
        description="나와 상대방의 큐브 티켓 현황을 입력하면,\n같이 뺄 수 있는 최적의 판수를 딱딱 정해드립니다.",
        color=0x2B2D31
    )
    await ctx.send(embed=embed, view=CubeView())


# =========================
# 실행
# =========================
bot.run(config.DISCORD_TOKEN)
