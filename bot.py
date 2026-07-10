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
# 📊 [신규] 로스트아크 시너지 데이터베이스
# =========================
SYNERGY_DATA = {
    "디스트로이어": "🛡️ 방깎 / 🔨 무력화",
    "버서커": "💥 피증",
    "워로드": "🛡️ 방깎 / 📐 백헤드 피증 / 🔰 받피감 / 📉 공깎 (고기: 방깎 제외 / 전태: 방깎 포함)",
    "홀리나이트": "⚡ 치피증",
    "슬레이어": "💥 피증",
    "발키리": "⚡ 치피증",
    "기공사": "⚔️ 공증 / 🔰 받피감 / 📉 공깎",
    "배틀마스터": "🎯 치적 / 🏃 공이속",
    "인파이터": "💥 피증 / 🔨 무력화",
    "창술사": "⚡ 치피증",
    "브레이커": "💥 피증",
    "스트라이커": "🎯 치적 / 💨 공속",
    "데빌헌터": "🎯 치적",
    "블래스터": "🛡️ 방깎 / 🔨 무력화",
    "스카우터": "⚔️ 공증",
    "호크아이": "💥 피증 / 📉 공깎 / 🏃 두동은 이속 추가",
    "건슬링어": "🎯 치적",
    "바드": "🛡️ 방깎 / 💨 공속 / 📉 공깎 / 🧪 마회 / 🔰 뎀감",
    "서머너": "🛡️ 방깎 / 🧪 마회",
    "소서리스": "💥 피증",
    "아르카나": "🎯 치적",
    "데모닉": "💥 피증",
    "리퍼": "🛡️ 방깎",
    "블레이드": "📐 백헤드 피증 / 🏃 공이속 / 📉 공깎",
    "소울이터": "💥 피증",
    "기상술사": "🎯 치적 / 📉 공깎 / 🏃 질풍은 공이속 추가",
    "도화가": "🛡️ 방깎 / 🔰 받피감 / 💨 공속 / 🧪 마회",
    "환수사": "🛡️ 방깎",
    "가디언나이트": "💥 피증"
}

# 레이드 컨닝페이퍼 데이터베이스
RAID_CHEAT_SHEETS = {
    "카멘": "https://example.com/kamen_image.png",       
    "에키드나": "https://example.com/echidna_image.png", 
    "베히모스": "https://example.com/behemoth_image.png", 
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
    except:
        return None

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
                if clean_val:
                    total_power = f"{int(float(clean_val)):,}"
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
# ✨ [신규] 시너지 확인 명령어
# =========================
@bot.command(name="시너지")
async def show_synergy(ctx, job_name: str = None):
    # 1. 특정 직업을 검색했을 때 (예: !시너지 디트, !시너지 바드)
    if job_name:
        # 입력된 글자가 포함된 직업 매칭 (ex: '기상' 치면 '기상술사' 매칭)
        matched_job = None
        for key in SYNERGY_DATA.keys():
            if job_name in key:
                matched_job = key
                break

        if matched_job:
            embed = discord.Embed(
                title=f"✨ {matched_job} 시너지 정보",
                description=f"**{SYNERGY_DATA[matched_job]}**",
                color=0x5865F2
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ `{job_name}` 직업을 찾을 수 없습니다. 정확한 이름을 입력해 주세요!")
        return

    # 2. 그냥 !시너지 만 쳤을 때 전체 리스트 노출
    embed = discord.Embed(title="⚔️ 로스트아크 전 직업 시너지 표", color=0x2B2D31)
    
    # 디스코드 가독성을 위해 6개씩 끊어서 필드에 이쁘게 담아줍니다.
    jobs = list(SYNERGY_DATA.keys())
    chunks = [jobs[i:i + 6] for i in range(0, len(jobs), 6)]
    
    for i, chunk in enumerate(chunks):
        chunk_text = ""
        for job in chunk:
            chunk_text += f"• **{job}**: {SYNERGY_DATA[job]}\n"
        embed.add_field(name=f"목록 ({i+1})", value=chunk_text, inline=False)
        
    embed.set_footer(text="💡 특정 직업만 보려면 [!시너지 직업명]을 입력하세요. (예: !시너지 워로드)")
    await ctx.send(embed=embed)


# =========================
# 📸 로아 레이드 컨닝페이퍼 명령어
# =========================
@bot.command(name="컨닝", aliases=["컷", "기믹"])
async def show_cheat_sheet(ctx, raid_name: str = None):
    if not raid_name:
        available_raids = ", ".join([f"`{k}`" for k in RAID_CHEAT_SHEETS.keys()])
        await ctx.send(f"❌ 사용법: `!컨닝 [레이드이름]`\nℹ️ 현재 등록된 레이드: {available_raids}")
        return

    if raid_name in RAID_CHEAT_SHEETS:
        image_url = RAID_CHEAT_SHEETS[raid_name]
        embed = discord.Embed(title=f"🗺️ {raid_name} 레이드 컨닝페이퍼 (공략)", color=0x2B2D31)
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ `{raid_name}` 레이드는 아직 컨닝페이퍼가 등록되지 않았습니다.")


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
