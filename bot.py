import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOSTARK_API_KEY = os.getenv("LOSTARK_API_KEY")

if LOSTARK_API_KEY:
    LOSTARK_API_KEY = str(LOSTARK_API_KEY).strip().replace('"', '').replace("'", "").replace("bearer ", "")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# 🏛️ 낙원 지옥 5층 전직업 스킬코드 데이터베이스
# =========================
NAKWON_SKILL_CODES = {
    "디스트로이어": "코드_디스트로이어_낙원_지옥_5층_샘플코드12345",
    "버서커": "코드_버서커_낙원_지옥_5층_샘플코드12345",
    "워로드": "코드_워로드_낙원_지옥_5층_샘플코드12345",
    "홀리나이트": "코드_홀리나이트_낙원_지옥_5층_샘플코드12345",
    "슬레이어": "코드_슬레이어_낙원_지옥_5층_샘플코드12345",
    "발키리": "코드_발키리_낙원_지옥_5층_샘플코드12345",
    "기공사": "코드_기공사_낙원_지옥_5층_샘플코드12345",
    "배틀마스터": "코드_배틀마스터_낙원_지옥_5층_샘플코드12345",
    "인파이터": "코드_인파이터_낙원_지옥_5층_샘플코드12345",
    "창술사": "코드_창술사_낙원_지옥_5층_샘플코드12345",
    "브레이커": "코드_브레이커_낙원_지옥_5층_샘플코드12345",
    "스트라이커": "코드_스트라이커_낙원_지옥_5층_샘플코드12345",
    "데빌헌터": "코드_데빌헌터_낙원_지옥_5층_샘플코드12345",
    "블래스터": "코드_블래스터_낙원_지옥_5층_샘플코드12345",
    "스카우터": "코드_스카우터_낙원_지옥_5층_샘플코드12345",
    "호크아이": "코드_호크아이_낙원_지옥_5층_샘플코드12345",
    "건슬링어": "코드_건슬링어_낙원_지옥_5층_샘플코드12345",
    "바드": "코드_바드_낙원_지옥_5층_샘플코드12345",
    "서머너": "코드_서머너_낙원_지옥_5층_샘플코드12345",
    "소서리스": "코드_소서리스_낙원_지옥_5층_샘플코드12345",
    "아르카나": "코드_아르카나_낙원_지옥_5층_샘플코드12345",
    "데모닉": "코드_데모닉_낙원_지옥_5층_샘플코드12345",
    "리퍼": "코드_리퍼_낙원_지옥_5층_샘플코드12345",
    "블레이드": "코드_블레이드_낙원_지옥_5층_샘플코드12345",
    "소울이터": "코드_소울이터_낙원_지옥_5층_샘플코드12345",
    "기상술사": "코드_기상술사_낙원_지옥_5층_샘플코드12345",
    "도화가": "코드_도화가_낙원_지옥_5층_샘플코드12345",
    "환수사": "코드_환수사_낙원_지옥_5층_샘플코드12345",
    "가디언나이트": "코드_가디언나이트_낙원_지옥_5층_샘플코드12345"
}

# 📊 로스트아크 시너지 데이터베이스
SYNERGY_DATA = {
    "디스트로이어": "🛡️ 방깎 / 🔨 무력화", "버서커": "💥 피증",
    "워로드": "🛡️ 방깎 / 📐 백헤드 피증 / 🔰 받피감 / 📉 공깎 (고기: 방깎 제외 / 전태: 방깎 포함)",
    "홀리나이트": "⚡ 치피증", "슬레이어": "💥 피증", "발키리": "⚡ 치피증",
    "기공사": "⚔️ 공증 / 🔰 받피감 / 📉 공깎", "배틀마스터": "🎯 치적 / 🏃 공이속",
    "인파이터": "💥 피증 / 🔨 무력화", "창술사": "⚡ 치피증", "브레이커": "💥 피증",
    "스트라이커": "🎯 치적 / 💨 공속", "데빌헌터": "🎯 치적", "블래스터": "🛡️ 방깎 / 🔨 무력화",
    "스카우터": "⚔️ 공증", "호크아이": "💥 피증 / 📉 공깎 / 🏃 두동은 이속 추가", "건슬링어": "🎯 치적",
    "바드": "🛡️ 방깎 / 💨 공속 / 📉 공깎 / 🧪 마회 / 🔰 뎀감", "서머너": "🛡️ 방깎 / 🧪 마회",
    "소서리스": "💥 피증", "아르카나": "🎯 치적", "데모닉": "💥 피증", "리퍼": "🛡️ 방깎",
    "블레이드": "📐 백헤드 피증 / 🏃 공이속 / 📉 공깎", "소울이터": "💥 피증",
    "기상술사": "🎯 치적 / 📉 공깎 / 🏃 질풍은 공이속 추가", "도화가": "🛡️ 방깎 / 🔰 받피감 / 💨 공속 / 🧪 마회",
    "환수사": "🛡️ 방깎", "가디언나이트": "💥 피증"
}


def get_character_profile(character_name):
    try:
        if not LOSTARK_API_KEY: return None
        headers = {"accept": "application/json", "authorization": f"bearer {LOSTARK_API_KEY}"}
        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}/profiles"
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# =========================
# 🔍 정보 검색 명령어
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 데이터를 가져오는 중...")
    profile = get_character_profile(character_name)
    if not profile:
        await status_msg.edit(content="❌ 캐릭터 정보를 가져오지 못했습니다.")
        return
    try:
        char_name = profile.get("CharacterName", character_name)
        char_class = profile.get("CharacterClassName", "알 수 없음")
        title = profile.get("Title") or "없음"
        guild_name = profile.get("GuildName") or "없음"
        guild_rank = profile.get("GuildMemberGrade") or ""
        raw_item_lvl = profile.get("ItemMaxLevel") or profile.get("ItemAvgLevel") or "0"
        item_lvl = str(raw_item_lvl).replace(",", "")
        exp_lvl = profile.get("CharacterLevel", "0")
        exp_exp = profile.get("ExpeditionLevel", "0")
        
        total_power = "정보 없음"
        stats_list = profile.get("Stats") or []
        for stat in stats_list:
            stat_type = str(stat.get("Type", "")).strip()
            stat_val = str(stat.get("Value", "")).strip()
            if "전투력" in stat_type or stat_type == "전투력":
                clean_val = re.sub(r'[^\d.]', '', stat_val)
                if clean_val: total_power = f"{int(float(clean_val)):,}"
                break

        embed = discord.Embed(title=f"🛡️ {char_name} ({char_class} / {title})", color=0x2B2D31)
        if profile.get("CharacterImage"): embed.set_thumbnail(url=profile["CharacterImage"])
        embed.add_field(name="🏰 소속 길드", value=f"`{guild_name}` {guild_rank}", inline=True)
        embed.add_field(name="✨ 원정대 레벨", value=f"Lv.{exp_exp}", inline=True)
        embed.add_field(name="⚔️ 전투 레벨", value=f"Lv.{exp_lvl}", inline=True)
        embed.add_field(name="💎 아이템 레벨", value=f"**{item_lvl}**", inline=True)
        embed.add_field(name="🔥 전투력", value=f"**{total_power}**", inline=True)
        embed.add_field(name="ㅤ", value="ㅤ", inline=True)
        await status_msg.delete()
        await ctx.send(embed=embed)
    except Exception as e:
        await status_msg.edit(content="❌ 데이터 파싱 중 오류가 발생했습니다.")


# =========================
# 🎯 낙원 스킬코드 명령어
# =========================
@bot.command(name="낙원")
async def show_nakwon_code(ctx, job_name: str = None):
    if not job_name:
        available_jobs = ", ".join([f"`{k}`" for k in NAKWON_SKILL_CODES.keys()])
        await ctx.send(f"❌ 사용법: `!낙원 [직업명]`\nℹ️ 등록된 직업: {available_jobs}")
        return

    matched_job = None
    for key in NAKWON_SKILL_CODES.keys():
        if job_name in key: matched_job = key; break

    if matched_job:
        code = NAKWON_SKILL_CODES[matched_job]
        embed = discord.Embed(title=f"🌊 낙원 5층 {matched_job} 아크 패시브 스킬코드", color=0x00A3FF)
        embed.add_field(name="📋 복사용 스킬코드", value=f"```{code}```", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ `{job_name}` 직업의 낙원 스킬코드를 찾을 수 없습니다.")


# =========================
# 💰 [신규] lo4.app 지옥 보상 효율 명령어
# =========================
@bot.command(name="보상")
async def show_hell_reward(ctx, level: str = None, floor_or_stage: int = None):
    if not level or level not in ["1640", "1700", "1730"]:
        await ctx.send("❌ 사용법: `!보상 [레벨]` 또는 `!보상 [레벨] [층수/단계]`\nℹ️ 입력 가능 레벨: `1640`, `1700`, `1730` (ex: `!보상 1640 50`)")
        return

    # 층수 입력을 단게로 치환 (ex: 55층 -> 5단계, 단독 단계입력 0~10도 인정)
    stage = 0
    display_text = "전 구간 공통"
    if floor_or_stage is not None:
        if floor_or_stage >= 11:
            stage = floor_or_stage // 10
            display_text = f"{floor_or_stage}층 ({stage}단계)"
        else:
            stage = floor_or_stage
            display_text = f"{stage}단계 (~{stage}9층)"

    embed = discord.Embed(
        title=f"🔥 낙원 지옥 [{level}레벨] {display_text} 보상 선택 가이드",
        description="[lo4.app/tools/hell-reward](https://lo4.app/tools/hell-reward) 데이터 기반 최적 효율 정산",
        color=0xE91E63
    )

    if level == "1640":
        embed.add_field(name="💎 압도적 1티어 추천", value="⭐ **어빌리티 스톤 키트**\n(개당 골드 가치 환산 시 가장 독보적인 가치를 가집니다.)", inline=False)
        embed.add_field(name="⚔️ 2티어 추천 (필요에 따라 선택)", value="• **특수 재련 재료 상자** (스펙업 연장선)\n• **혼돈의 돌 카테고리**\n• **재련 보조 상자** (용숨/빙숨)", inline=False)
        embed.add_field(name="📉 비추천 (하위 효율)", value="• 귀속 골드, 운명의 돌, 유물 팔찌, 운명의 돌파석", inline=False)
    
    elif level == "1700":
        embed.add_field(name="💎 압도적 1티어 추천", value="⭐ **어빌리티 스톤 키트** & **고대 팔찌**\n(1700구간 진입 시 팔찌가 고대로 업그레이드되어 가치가 폭등합니다.)", inline=False)
        embed.add_field(name="⚔️ 2티어 추천", value="• **특수 재련 재료 상자**\n• **운명의 돌** (무료 카르마 진화용)\n• **젬 랜덤 상자** (희귀~영웅 등급으로 재편되어 효율 상승)", inline=False)
        embed.add_field(name="📉 변경점 및 주의사항", value="• 혼돈의 돌 대신 운명의 돌이 등장합니다.\n• 상급 재련보조 상자가 목록에서 제외됩니다.", inline=False)

    elif level == "1730":
        embed.add_field(name="💎 최고 효율 추천 (다음 티어 대비)", value="⭐ **젬 선택 상자 (고급 제거 버전)**\n(1730층은 젬 선택 상자 개수가 대폭 증가하여 골드 기대값이 매우 높습니다.)\n⭐ **고대 팔찌**", inline=False)
        embed.add_field(name="⚔️ 2티어 추천", value="• **특수 재련 재료 상자**\n• 다음 티어 재료 (**파괴석 결정 / 상급 아비도스** 등)", inline=False)
        embed.add_field(name="⚠️ 삭제 및 변경 카테고리", value="• 수호석/파괴석 선택 및 돌파석 카테고리가 완전히 삭제되었습니다.\n• 젬 랜덤 상자가 삭제되고 **선택 상자**로 대체되었습니다.", inline=False)

    embed.set_footer(text="💡 팁: 11의 배수층 럭키방이나 10% 확률로 기본 재료가 10배가 되는 '풍요로운 상자' 변수를 노려보세요!")
    await ctx.send(embed=embed)


# =========================
# ✨ 시너지 확인 명령어
# =========================
@bot.command(name="시너지")
async def show_synergy(ctx, job_name: str = None):
    if job_name:
        matched_job = None
        for key in SYNERGY_DATA.keys():
            if job_name in key: matched_job = key; break
        if matched_job:
            embed = discord.Embed(title=f"✨ {matched_job} 시너지 정보", description=f"**{SYNERGY_DATA[matched_job]}**", color=0x5865F2)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ `{job_name}` 직업을 찾을 수 없습니다.")
        return

    embed = discord.Embed(title="⚔️ 로스트아크 전 직업 시너지 표", color=0x2B2D31)
    jobs = list(SYNERGY_DATA.keys())
    chunks = [jobs[i:i + 6] for i in range(0, len(jobs), 6)]
    for i, chunk in enumerate(chunks):
        chunk_text = ""
        for job in chunk: chunk_text += f"• **{job}**: {SYNERGY_DATA[job]}\n"
        embed.add_field(name=f"목록 ({i+1})", value=chunk_text, inline=False)
    embed.set_footer(text="💡 특정 직업만 보려면 [!시너지 직업명]을 입력하세요.")
    await ctx.send(embed=embed)


# =========================
# 🎲 캐릭터별 큐브 매칭 정산
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 캐릭터별 큐브 매칭 정산"):
    my_tickets = discord.ui.TextInput(label="내 캐릭별 티켓 현황", style=discord.TextStyle.long, required=True)
    partner_tickets = discord.ui.TextInput(label="상대방 캐릭별 티켓 현황", style=discord.TextStyle.long, required=True)

    def parse_tickets_by_char(self, text):
        data = {4: {}, 3: {}, 2: {}, 1: {}}
        lines = text.strip().split('\n')
        for line in lines:
            if not line.strip(): continue
            match = re.search(r'([1-4])[^\d]*(\d+)', line)
            if match:
                stage = int(match.group(1))
                count = int(match.group(2))
                char_name = line.split(match.group(0))[0].strip()
                if not char_name: char_name = f"캐릭_{stage}"
                data[stage][char_name] = data[stage].get(char_name, 0) + count
        return data

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        me = self.parse_tickets_by_char(self.my_tickets.value)
        partner = self.parse_tickets_by_char(self.partner_tickets.value)
        embed = discord.Embed(title="📊 캐릭터별 최적 큐브 동선 설계", color=0x00FFFF)
        
        has_data = False
        for stage in [4, 3, 2, 1]:
            my_chars = {k: v for k, v in me[stage].items() if v > 0}
            partner_chars = {k: v for k, v in partner[stage].items() if v > 0}
            if not my_chars and not partner_chars: continue
            has_data = True
            stage_text = "**🔹 [3배 소모 조합]**\n"
            triple_found = False
            for m_char in list(my_chars.keys()):
                for p_char in list(partner_chars.keys()):
                    if my_chars[m_char] >= 3 and partner_chars[p_char] >= 3:
                        pan = min(my_chars[m_char] // 3, partner_chars[p_char] // 3)
                        if pan > 0:
                            stage_text += f"➔ 나의 **[{m_char}]** ⚔️ 상대 **[{p_char}]** ➜ **3배로 {pan}판**\n"
                            my_chars[m_char] -= pan * 3
                            partner_chars[p_char] -= pan * 3
                            triple_found = True
            if not triple_found: stage_text += "➔ 3배 조합이 없습니다.\n"

            stage_text += "\n**🔸 [1배 소모 및 잔여 믹스]**\n"
            single_found = False
            my_remains = {k: v for k, v in my_chars.items() if v > 0}
            partner_remains = {k: v for k, v in partner_chars.items() if v > 0}
            for m_char in list(my_remains.keys()):
                for p_char in list(partner_remains.keys()):
                    if my_remains[m_char] > 0 and partner_remains[p_char] > 0:
                        pan = min(my_remains[m_char], partner_remains[p_char])
                        stage_text += f"➔ 나의 **[{m_char}]** ({my_remains[m_char]}장) ⚔️ 상대 **[{p_char}]** ({partner_remains[p_char]}장) ➜ **1배로 {pan}판**\n"
                        my_remains[m_char] -= pan
                        partner_remains[p_char] -= pan
                        single_found = True
            if not single_found and triple_found: stage_text += "➔ 깔끔하게 정산되었습니다!\n"
            embed.add_field(name=f"▶️ {stage}해금 큐브 가이드", value=stage_text + "─", inline=False)

        if not has_data:
            await interaction.followup.send("❌ 티켓 데이터를 파싱하지 못했습니다.")
            return
        await interaction.followup.send(embed=embed)

class CubeView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="큐브 정산하기", style=discord.ButtonStyle.blurple, custom_id="cube_calc_btn")
    async def cube_calc(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(CubeCalculatorModal())


# =========================
# 길드 인증 기능
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(label="캐릭터 이름", placeholder="캐릭터 이름 입력", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        profile = get_character_profile(self.character_name.value)
        if not profile:
            await interaction.followup.send("❌ 캐릭터 정보를 찾을 수 없습니다.")
            return
        guild = interaction.guild
        member = guild.get_member(interaction.user.id)
        if member is None: return

        char_name = profile["CharacterName"]
        char_class = profile["CharacterClassName"]
        char_guild = profile.get("GuildName") or ""

        try: await member.edit(nick=f"{char_name}/{char_class}")
        except: pass

        roles_to_add = [char_class]
        config_guild = os.getenv("GUILD_NAME", "")
        if char_guild.strip() == config_guild.strip() if config_guild else False:
            member_role = os.getenv("MEMBER_ROLE", "")
            if member_role: roles_to_add.append(member_role)
        else:
            roles_to_add.append(os.getenv("GUEST_ROLE", "외부인"))

        for r_name in roles_to_add:
            role = discord.utils.get(guild.roles, name=r_name)
            if role: await member.add_roles(role)

        embed = discord.Embed(title="✅ 인증 완료", description=f"**{char_name}**님 환영합니다.", color=0x57F287)
        await interaction.followup.send(embed=embed)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(VerifyModal())


# =========================
# 진입점 및 이벤트
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(CubeView())
    print(f"✅ 로그인 완료: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

@bot.command()
async def 인증패널(ctx): await ctx.send(embed=discord.Embed(title="로스트아크 길드 인증", color=0x2B2D31), view=VerifyView())
@bot.command()
async def 큐브계산기(ctx): await ctx.send(embed=discord.Embed(title="🎲 큐브 매칭", color=0x2B2D31), view=CubeView())

bot.run(DISCORD_TOKEN)
