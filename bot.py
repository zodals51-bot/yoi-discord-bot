import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
from dotenv import load_dotenv  # .env 파일을 직접 읽기 위한 모듈

# .env 파일 로드
load_dotenv()

# 환경 변수에서 토큰 및 API 키 직접 가져오기 (따옴표나 bearer 자동 제거 공정 포함)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOSTARK_API_KEY = os.getenv("LOSTARK_API_KEY")

if LOSTARK_API_KEY:
    LOSTARK_API_KEY = str(LOSTARK_API_KEY).strip().replace('"', '').replace("'", "").replace("bearer ", "")

# =========================
# 봇 기본 설정 및 권한
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# 로스트아크 API 연동 함수군
# =========================
def get_character_info(character_name):
    """단일 프로필 조회 (길드 인증용)"""
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
        if r.status_code != 200:
            return None

        data = r.json()
        if not data or "CharacterName" not in data:
            return None

        return {
            "name": data["CharacterName"],
            "class": data["CharacterClassName"],
            "guild": data.get("GuildName") or ""
        }
    except Exception as e:
        print("단일 프로필 API 오류:", e)
        return None


def get_full_armory(character_name):
    """로펙형 데이터 조회를 위한 통합 세팅 조회"""
    try:
        if not LOSTARK_API_KEY:
            print("❌ [로아 API 오류] .env 파일에서 LOSTARK_API_KEY를 찾을 수 없습니다.")
            return None

        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}"
        params = {"filters": "profiles|equipment|arkpassive|gems|cards"}
        
        current_headers = {
            "accept": "application/json",
            "authorization": f"bearer {LOSTARK_API_KEY}"
        }
        
        r = requests.get(url, headers=current_headers, params=params)
        
        if r.status_code == 401:
            print(f"❌ [로아 API 오류] 401 Unauthorized: .env의 API 키가 틀렸거나 만료되었습니다.")
            return None
        elif r.status_code == 404:
            print(f"❌ [로아 API 오류] 404 Not Found: '{character_name}' 캐릭터가 없습니다.")
            return None
        elif r.status_code != 200:
            print(f"❌ [로아 API 오류] 상태 코드 {r.status_code}: API 서버 연결 실패")
            return None

        return r.json()
    except Exception as e:
        print("종합 API 함수 내부 오류:", e)
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

        info = get_character_info(self.character_name.value)

        if not info:
            await interaction.followup.send("❌ 캐릭터 정보를 찾을 수 없습니다.")
            return

        guild = interaction.guild
        member = guild.get_member(interaction.user.id)

        if member is None:
            await interaction.followup.send("❌ 멤버 정보를 불러올 수 없습니다.")
            return

        try:
            await member.edit(nick=f"{info['name']}/{info['class']}")
        except Exception as e:
            print("닉네임 변경 실패:", e)

        roles_to_add = [info["class"]]
        embed_title = "✅ 인증 완료"
        embed_color = 0x57F287
        embed_description = f"**{info['name']}**님, 인증이 완료되었습니다."

        # .env 혹은 환경변수 기반으로 유연하게 처리 (없으면 기본값)
        config_guild = os.getenv("GUILD_NAME", "")
        is_guild_member = info["guild"].strip() == config_guild.strip() if config_guild else False

        if is_guild_member:
            member_role = os.getenv("MEMBER_ROLE", "")
            if member_role: roles_to_add.append(member_role)
        else:
            guest_role_name = os.getenv("GUEST_ROLE", "외부인")
            roles_to_add.append(guest_role_name)
            current_guild = info['guild'] if info['guild'] else '없음'
            embed_title = "ℹ 외부인 인증 완료"
            embed_color = 0x3498DB
            embed_description = f"**{info['name']}**님은 외부인(지인)으로 인증되었습니다.\n(조회된 길드: {current_guild})"

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
        embed.add_field(name="캐릭터명", value=info["name"], inline=True)
        embed.add_field(name="직업", value=info["class"], inline=True)
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
# 🔍 로펙 스타일 캐릭터 스펙 검색 기능
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return

    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 로펙형 스펙 세팅을 파싱하고 있습니다...")
    
    try:
        armory = get_full_armory(character_name)
        if not armory or not armory.get("Profile"):
            await status_msg.edit(content="❌ 캐릭터 정보를 가져오지 못했습니다. .env의 API 키 값 자체를 아예 새로 발급받아 교체해 보시는 것을 권장합니다.")
            return

        profile = armory["Profile"]
        equipment = armory.get("Equipment") or []
        ark_passive = armory.get("ArkPassive") or {}
        gems = armory.get("Gems") or {}
        cards = armory.get("Cards") or {}

        embed = discord.Embed(
            title=f"🛡️ {profile.get('CharacterName', character_name)} 스펙 진단 결과",
            description=f"**{profile.get('CharacterClassName', '알 수 없음')}** | 아이템 레벨: `Lv.{profile.get('ItemMaxLevel', '정보 없음')}`",
            color=0x2B2D31
        )
        
        if profile.get("CharacterImage"):
            embed.set_thumbnail(url=profile["CharacterImage"])

        # 1. 전투 특성
        stats_text = ""
        for stat in profile.get("Stats", []):
            if stat.get("Type") in ["치명", "특화", "신속"]:
                stats_text += f"• {stat['Type']}: `{stat['Value']}`\n"
        if not stats_text:
            stats_text = "• 특성 정보 없음"
        embed.add_field(name="📊 주 스탯 및 전투 특성", value=stats_text, inline=True)

        # 2. 아크 그리드
        ark_text = ""
        if ark_passive.get("IsAvailable"):
            ark_text += "• 상태: **아크 패시브 가동 중**\n"
            if ark_passive.get("Points"):
                for pt in ark_passive["Points"]:
                    ark_text += f"- {pt.get('Name')}: `{pt.get('Value')} pt`\n"
        else:
            ark_text = "• 상태: 비활성화 (기존 세팅)"
        embed.add_field(name="🧬 아크 그리드(패시브)", value=ark_text, inline=True)

        # 3. 보석
        gem_list = gems.get("Gems") or []
        if gem_list:
            gem_summary = {}
            for g in gem_list:
                lvl = g.get("Level", 0)
                g_name = g.get("Name", "")
                g_type = "멸/겁화" if "피해" in g_name else "홍/작열"
                key = f"T{g.get('Tier', 3)} {lvl}레벨 {g_type}"
                gem_summary[key] = gem_summary.get(key, 0) + 1
            gem_text = "\n".join([f"• {k} × {v}개" for k, v in sorted(gem_summary.items(), reverse=True)])
        else:
            gem_text = "• 장착된 보석이 없습니다."
        embed.add_field(name="💎 보석 장착 현황", value=gem_text, inline=False)

        # 4. 장비
        weapon_info = "• 무기 정보 없음"
        armor_count = 0
        acc_list = []
        for eq in equipment:
            eq_type = eq.get("Type")
            eq_name = eq.get("Name")
            if eq_type == "무기":
                weapon_info = f"• {eq_name}"
            elif eq_type in ["투구", "견갑", "상의", "하의", "장갑"]:
                armor_count += 1
            elif eq_type in ["목걸이", "귀걸이", "반지", "브레이서"]:
                acc_list.append(f"• {eq_type}: {eq_name}")

        embed.add_field(name="⚔️ 장비 요약", value=f"{weapon_info}\n• 방어구: `{armor_count}/5` 부위", inline=True)
        embed.add_field(name="💍 악세사리 세팅", value="\n".join(acc_list) if acc_list else "• 미착용", inline=True)

        # 5. 카드
        card_effects = cards.get("Effects") or []
        if card_effects:
            try:
                active_set = card_effects[-1].get("Items", [dict()])[-1].get("Name", "세트 효과 없음")
                card_text = f"• 활성화 효과: **{active_set}**"
            except:
                card_text = "• 카드 효과 파싱 실패"
        else:
            card_text = "• 활성화된 카드 세트 효과가 없습니다."
        embed.add_field(name="🃏 카드 세트 효과", value=card_text, inline=False)

        await status_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        print("명령어 내부 오류:", e)
        await status_msg.edit(content="❌ 봇 내부 연동 에러가 발생했습니다.")


# =========================
# 봇 실행 이벤트
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
    embed = discord.Embed(title="로스트아크 길드 인증", description="아래 버튼을 눌러 인증하세요", color=0x2B2D31)
    await ctx.send(embed=embed, view=VerifyView())


@bot.command()
async def 큐브계산기(ctx):
    embed = discord.Embed(title="🎲 큐브 2인 다캐릭 통합 매칭", description="티켓 현황을 입력하세요.", color=0x2B2D31)
    await ctx.send(embed=embed, view=CubeView())

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ [디스코드 오류] .env 파일에서 DISCORD_TOKEN을 읽어오지 못했습니다.")
