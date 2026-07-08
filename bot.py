import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 다이렉트 연동 (따옴표 및 bearer 자동 제거 공정 포함)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOSTARK_API_KEY = os.getenv("LOSTARK_API_KEY")

if LOSTARK_API_KEY:
    LOSTARK_API_KEY = str(LOSTARK_API_KEY).strip().replace('"', '').replace("'", "").replace("bearer ", "")

# 디스코드 인텐트 설정
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# 로스트아크 API 연동 함수군
# =========================
def get_character_profile(character_name):
    """전투정보실 스타일 출력을 위한 프로필 집중 파싱"""
    try:
        if not LOSTARK_API_KEY:
            print("❌ [로아 API 오류] .env 파일에서 LOSTARK_API_KEY를 찾을 수 없습니다.")
            return None
            
        headers = {
            "accept": "application/json",
            "authorization": f"bearer {LOSTARK_API_KEY}"
        }
        
        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}/profiles"

        r = requests.get(url, headers=headers)
        if r.status_code == 401:
            print("❌ [로아 API 오류] 401 Unauthorized: API 키가 올바르지 않거나 만료되었습니다.")
            return None
        elif r.status_code != 200:
            print(f"❌ [로아 API 오류] 상태 코드: {r.status_code}")
            return None

        data = r.json()
        if not data or "CharacterName" not in data:
            return None

        return data
    except Exception as e:
        print("프로필 API 오류:", e)
        return None


# =========================
# 길드 인증 기능 (모달 및 뷰)
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(
        label="캐릭터 이름",
        placeholder="캐릭터 이름 입력",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        profile = get_character_profile(self.character_name.value)

        if not profile:
            await interaction.followup.send("❌ 캐릭터 정보를 찾을 수 없습니다.")
            return

        guild = interaction.guild
        member = guild.get_member(interaction.user.id)

        if member is None:
            await interaction.followup.send("❌ 멤버 정보를 불러올 수 없습니다.")
            return

        char_name = profile["CharacterName"]
        char_class = profile["CharacterClassName"]
        char_guild = profile.get("GuildName") or ""

        try:
            await member.edit(nick=f"{char_name}/{char_class}")
        except Exception as e:
            print("닉네임 변경 실패 (봇 권한 위계 확인 필요):", e)

        roles_to_add = [char_class]
        embed_title = "✅ 인증 완료"
        embed_color = 0x57F287
        embed_description = f"**{char_name}**님, 인증이 완료되었습니다."

        config_guild = os.getenv("GUILD_NAME", "")
        is_guild_member = char_guild.strip() == config_guild.strip() if config_guild else False

        if is_guild_member:
            member_role = os.getenv("MEMBER_ROLE", "")
            if member_role: roles_to_add.append(member_role)
        else:
            guest_role_name = os.getenv("GUEST_ROLE", "외부인")
            roles_to_add.append(guest_role_name)
            current_guild = char_guild if char_guild else '없음'
            embed_title = "ℹ 외부인 인증 완료"
            embed_color = 0x3498DB
            embed_description = f"**{char_name}**님은 외부인(지인)으로 인증되었습니다.\n(조회된 길드: {current_guild})"

        for role_name in roles_to_add:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role)
                except Exception as e:
                    print(f"❌ 역할 지급 실패 ({role_name}):", e)

        wait_role_name = os.getenv("WAIT_ROLE", "")
        if wait_role_name:
            wait_role = discord.utils.get(guild.roles, name=wait_role_name)
            if wait_role:
                try:
                    await member.remove_roles(wait_role)
                except Exception as e:
                    print("WAIT_ROLE 제거 실패:", e)

        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="캐릭터명", value=char_name, inline=True)
        embed.add_field(name="직업", value=char_class, inline=True)
        await interaction.followup.send(embed=embed)


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())


# =========================
# 🎲 2인 다캐릭 통합 큐브 계산기
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 2인 다캐릭 통합 큐브 정산"):
    my_tickets = discord.ui.TextInput(
        label="내 모든 캐릭터 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n환수사 4해금 3 / 3해금 2",
        style=discord.TextStyle.long,
        required=True
    )
    partner_tickets = discord.ui.TextInput(
        label="상대방 모든 캐릭터 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n죽창 3해금 9",
        style=discord.TextStyle.long,
        required=True
    )

    def parse_and_sum_tickets(self, text):
        total = {4: 0, 3: 0, 2: 0, 1: 0}
        matches = re.findall(r'([1-4])[^\d]*(\d+)', text)
        for stage, count in matches:
            total[int(stage)] += int(count)
        return total

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        me = self.parse_and_sum_tickets(self.my_tickets.value)
        partner = self.parse_and_sum_tickets(self.partner_tickets.value)

        embed = discord.Embed(title="📊 2인 다캐릭 통합 큐브 정산 가이드", color=0x00FFFF)
        embed.description = "두 분이 보유한 **모든 캐릭터의 티켓 합산량**을 기준으로 한 최적 동선입니다.\n"

        has_data = False

        for stage in [4, 3, 2, 1]:
            start_me = me[stage]
            start_partner = partner[stage]

            if start_me == 0 and start_partner == 0:
                continue

            current_me = start_me
            current_partner = start_partner
            
            stage_text = f"**통합 총량:** 나 [{start_me}장] vs 상대방 [{start_partner}장]\n"

            me_triples = current_me // 3
            partner_triples = current_partner // 3
            common_triples = min(me_triples, partner_triples)

            if common_triples > 0:
                stage_text += f"➡️ **[3배 소모]** 캐릭 변경해가며 같이 **{common_triples}판** 진행\n"
                current_me -= common_triples * 3
                current_partner -= common_triples * 3
            else:
                stage_text += f"➡️ **[3배 소모]** 공통 판수가 없습니다.\n"

            common_singles = min(current_me, current_partner)
            if common_singles > 0:
                stage_text += f"➡️ **[1배 믹스]** 남은 티켓으로 같이 **{common_singles}판** 녹이기\n"
                current_me -= common_singles
                current_partner -= common_singles

            stage_text += "✨ **추천 루틴:** "
            actions = []
            if common_triples > 0: actions.append(f"3배로 {common_triples}판")
            if common_singles > 0: actions.append(f"1배로 {common_singles}판")
            
            if actions:
                stage_text += f"**{' ➡️ '.join(actions)}**을 같이 도는 것이 깔끔합니다.\n"
            else:
                stage_text += "함께 뺄 수 있는 조합이 없습니다.\n"

            embed.add_field(name=f"▶️ {stage}해금 에브니 큐브 통합 결과", value=stage_text + "─", inline=False)
            has_data = True

        if not has_data:
            await interaction.followup.send("❌ 입력 양식이 잘못되었습니다.")
            return

        await interaction.followup.send(embed=embed)


class CubeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="큐브 정산하기", style=discord.ButtonStyle.blurple, custom_id="cube_calc_btn")
    async def cube_calc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CubeCalculatorModal())


# =========================
# 🔍 템렙/전투력 집중 출력 스펙 검색 기능
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]` (예: `!정보 구워링`)")
        return

    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 전투정보실 데이터를 불러오는 중...")
    
    profile = get_character_profile(character_name)
    if not profile:
        await status_msg.edit(content="❌ 캐릭터 정보를 가져오지 못했습니다. .env의 API 키 세팅이나 캐릭터명을 확인하세요.")
        return

    try:
        char_name = profile.get("CharacterName", character_name)
        char_class = profile.get("CharacterClassName", "알 수 없음")
        title = profile.get("Title", "없음")
        guild_name = profile.get("GuildName") or "없음"
        guild_rank = profile.get("GuildMemberGrade") or ""
        
        item_lvl = profile.get("ItemMaxLevel", "0.00")
        exp_lvl = profile.get("CharacterLevel", "0")
        exp_exp = profile.get("ExpeditionLevel", "0")
        
        # 전투력 파싱 및 포맷팅 (, 추가)
        total_power = "정보 없음"
        for stat in profile.get("Stats", []):
            if stat.get("Type") == "전투력":
                total_power = f"{int(float(stat['Value'])):,}" if stat.get("Value") else "정보 없음"
                break

        # 전투정보실 레이아웃 기반 깔끔한 임베드 생성
        embed = discord.Embed(
            title=f"🛡️ {char_name} ({char_class} / {title})",
            color=0x2B2D31
        )
        
        if profile.get("CharacterImage"):
            embed.set_thumbnail(url=profile["CharacterImage"])

        # 정보 일렬 배치
        embed.add_field(name="🏰 소속 길드", value=f"`{guild_name}` {guild_rank}", inline=True)
        embed.add_field(name="✨ 원정대 레벨", value=f"Lv.{exp_exp}", inline=True)
        embed.add_field(name="⚔️ 전투 레벨", value=f"Lv.{exp_lvl}", inline=True)
        
        embed.add_field(name="💎 아이템 레벨", value=f"**{item_lvl}**", inline=True)
        embed.add_field(name="🔥 전투력", value=f"**{total_power}**", inline=True)
        embed.add_field(name="ㅤ", value="ㅤ", inline=True)  # 레이아웃 정렬 공백

        await status_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        print("명령어 내부 처리 오류:", e)
        await status_msg.edit(content="❌ 봇 내부 연동 에러가 발생했습니다.")


# =========================
# 봇 가동 및 명령어 연동 이벤트
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(CubeView())
    print(f"✅ 로그인 완료: {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


@bot.command()
async def 인증패널(ctx):
    embed = discord.Embed(
        title="로스트아크 길드 인증",
        description="아래 버튼을 눌러 인증하세요\n(지인분들도 동일하게 인증하시면 됩니다)",
        color=0x2B2D31
    )
    await ctx.send(embed=embed, view=VerifyView())


@bot.command()
async def 큐브계산기(ctx):
    embed = discord.Embed(
        title="🎲 큐브 2인 다캐릭 통합 매칭",
        description="나와 상대방의 모든 캐릭터 티켓 현황을 붙여넣으세요.",
        color=0x2B2D31
    )
    await ctx.send(embed=embed, view=CubeView())


if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ [디스코드 오류] .env 파일에서 DISCORD_TOKEN을 읽어오지 못했습니다.")
