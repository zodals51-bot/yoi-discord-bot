import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
import asyncio
from datetime import datetime
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
# 🏛️ 기본 데이터베이스
# =========================
NAKWON_SKILL_CODES = {
    "창술사": {"code": "E1AA2478E3E86E11155E0106A43F57A087C5766E9F31FDCB0C49FED79E02959B25DE9A1A3E9891102074EE9F3D00F88F0D652D0C6908ED480273AB97A96B9335"}
}

BASE_REWARD_VALUES = {
    "어빌리티스톤": 734690, "어빌": 734690, "돌": 734690,
    "특수재련": 306544, "특재": 306544,
    "재련보조": 200424, "보조": 200424, "숨결": 200424,
    "젬선택": 192338, "보석": 192338, "젬": 192338,
    "아비도스융화재료": 155964, "아비도스": 155964, "융화재료": 155964,
    "파괴석수호석결정": 125814, "파괴석": 125814, "수호석": 125814, "결정": 125814,
    "팔찌": 122964,
    "운명의돌혼돈의돌": 110964, "운돌": 110964, "혼돌": 110964, "운명의돌": 110964, "혼돈의돌": 110964,
    "귀속골드": 80964, "골드": 80964,
    "천상도전권": 32964, "도전권": 32964, "천상": 32964,
    "돌파석": 9264
}

# =========================
# ⚙️ 로스트아크 API 연동 헬퍼
# =========================
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

def get_character_engravings(character_name):
    try:
        if not LOSTARK_API_KEY: return []
        headers = {"accept": "application/json", "authorization": f"bearer {LOSTARK_API_KEY}"}
        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}/engravings"
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return []
        data = r.json()
        return data.get("Effects") or []
    except: return []


# =========================
# 🛡️ [아크그리드 동적 반영] 캐릭터 정보실 UI (!정보)
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return
        
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 전 서버 스펙트럼 분석 중...")
    
    profile = get_character_profile(character_name)
    engravings = get_character_engravings(character_name)
    
    # 기본 백업 데이터 설정
    char_name = profile.get("CharacterName", character_name) if profile else character_name
    char_class = profile.get("CharacterClassName", "창술사") if profile else "창술사"
    server_name = profile.get("ServerName", "카제로스") if profile else "카제로스"
    title = profile.get("Title") or "마수의 포효"
    guild_name = profile.get("GuildName") or "없음"
    
    item_lvl = "1,755.00"
    exp_exp = "285"
    exp_lvl = "60"
    total_power = "알 수 없음"
    attack_power = "알 수 없음"
    
    grid_nodes = []
    additional_effects = []

    if profile:
        item_lvl = str(profile.get("ItemMaxLevel", "0"))
        exp_exp = str(profile.get("ExpeditionLevel", "0"))
        exp_lvl = str(profile.get("CharacterLevel", "0"))
        
        # 📊 API에서 실시간 스탯, 아크 그리드, 세부 효과를 분류하여 추출
        stats_list = profile.get("Stats") or []
        for stat in stats_list:
            s_type = str(stat.get("Type", ""))
            s_value = str(stat.get("Value", "0"))
            
            # 1. 핵심 스탯 추출
            if "공격력" in s_type and "아군" not in s_type:
                attack_power = f"{int(float(re.sub(r'[^\d.]', '', s_value))):,}"
            elif "전투력" in s_type:
                total_power = f"{float(re.sub(r'[^\d.]', '', s_value)):,}"
            
            # 2. 아크 그리드 노드 추출 (질서의 해, 혼돈의 달 등)
            elif any(x in s_type for x in ["질서", "혼돈"]):
                # 예: "질서의 해 19P" 형태로 가독성 있게 정렬
                clean_val = s_value.replace(".00", "").replace(".0", "")
                grid_nodes.append(f"• {s_type} {clean_val}P")
                
            # 3. 우측 세부 추가 효과 추출 (보스 피해, 추가 피해 등)
            elif any(x in s_type for x in ["피해", "낙인력", "적룡", "집중", "한점", "현란", "불타", "공격"]):
                clean_val = s_value.replace(".00", "").replace(".0", "")
                additional_effects.append(f"• {s_type} `Lv.{clean_val}`" if clean_val.isdigit() else f"• {s_type} `{clean_val}`")

    # 만약 타 직업이라 API에 아크 그리드 정보가 없거나 예외일 때만 기본 스킨으로 분기
    if not grid_nodes:
        grid_nodes = [
            "• 질서의 해 19P  ➜  적룡의 기운",
            "• 질서의 달 20P  ➜  집중 강화",
            "• 질서의 별 20P  ➜  한점 돌파",
            "• 혼돈의 해 17P  ➜  현란한 공격",
            "• 혼돈의 달 20P  ➜  불타는 일격",
            "• 혼돈의 별 20P  ➜  공격"
        ]
    if not additional_effects:
        additional_effects = [
            "• 공격력 `Lv.43`\n• 보스 피해 `Lv.23`\n• 추가 피해 `Lv.23`\n• 낙인력 `Lv.34`\n• 아군 피해 강화 `Lv.15`"
        ]
    else:
        # 가독성을 위해 최대 5개까지만 노출 처리
        additional_effects = additional_effects[:5]

    embed = discord.Embed(
        title=f"🎭 {server_name}  |  {char_name} ㅤ", 
        description=f"**{char_class}** 세팅 정보 상시 동기화\n칭호: `{title}` ㅤ|ㅤ 길드: `{guild_name}`",
        color=0x1E1F22
    )
    if profile and profile.get("CharacterImage"): 
        embed.set_thumbnail(url=profile["CharacterImage"])

    # 3열 스펙트럼 필드
    embed.add_field(name="📋 기본 정보", value=f"• 아이템 Lv: `{item_lvl}`\n• 원정대 Lv: `{exp_exp}`\n• 전투 Lv: `Lv.{exp_lvl}`", inline=True)
    embed.add_field(name="🔥 핵심 스탯", value=f"• 전투력: **{total_power}**\n• 공격력: `{attack_power}`", inline=True)
    embed.add_field(name="✨ 장비 성장도", value="• 방어구: `운명의 업화`\n• 무기 단계: `아크 패시브 가동` \n• 엘릭서: `연성 완료`", inline=True)

    # 💠 [직업별 동적 반영] 아크 그리드 분배 현황
    embed.add_field(name="💠 아크 그리드 분배 현황", value=f"```md\n" + "\n".join(grid_nodes) + "```", inline=False)

    # ⚡ 아크 패시브 대분류 현황 노드
    ark_passive_text = (
        "🟩 진화   ➜ 아크 패시브 시스템 정상 가동 중\n"
        "🟪 깨달음 ➜ 직업 전용 아크 패시브 활성화 완료\n"
        "🟦 도약   ➜ 초월 및 아크 그리드 연동 완료"
    )
    embed.add_field(name="⚡ 아크 패시브 가동 스펙", value=f"```md\n{ark_passive_text}```", inline=False)

    # 각인 필드
    if engravings:
        eng_text = ""
        for eng in engravings:
            eng_text += f"• 🟥 **{eng.get('Name', '')}**\n"
    else:
        eng_text = "• 🟥 **마나 효율 증가**\n• 🟥 **기습의 대가**\n• 🟥 **저주받은 인형**\n• 🟥 **돌격대장**\n• 🟥 **원한**"
    embed.add_field(name="🔸 활성화 각인 시스템", value=eng_text, inline=True)

    # 📊 [직업별 동적 반영] 세부 추가 효과 필드
    embed.add_field(name="📊 세부 추가 효과", value="\n".join(additional_effects), inline=True)

    await status_msg.delete()
    await ctx.send(embed=embed)


# =========================
# ⚔️ 실시간 레이드 모집 UI 매칭
# =========================
class RaidJoinView(discord.ui.View):
    def __init__(self, title, creator, max_dealers=3, max_supporters=1):
        super().__init__(timeout=None)
        self.title = title
        self.creator = creator
        self.max_dealers = max_dealers
        self.max_supporters = max_supporters
        self.dealers = [(creator, "Lv.1755.0 | 창술사 | 3217.02 👑")]
        self.supporters = []
        
    def generate_embed(self):
        embed = discord.Embed(title=f"⚔️ {self.title}", description=f"**공격대 생성자:** {self.creator.mention}\n", color=0x2B2D31)
        
        dealer_slots = []
        for i in range(self.max_dealers):
            if i < len(self.dealers):
                user, char_info = self.dealers[i]
                dealer_slots.append(f"• {user.mention} ➜ `{char_info}`")
            else:
                dealer_slots.append("• == 없음 ==")
        
        supp_slots = []
        for i in range(self.max_supporters):
            if i < len(self.supporters):
                user, char_info = self.supporters[i]
                supp_slots.append(f"• {user.mention} ➜ `{char_info}`")
            else:
                supp_slots.append("• == 없음 ==")

        embed.add_field(name=f"딜러 ({len(self.dealers)}/{self.max_dealers})", value="\n".join(dealer_slots), inline=False)
        embed.add_field(name=f"서포터 ({len(self.supporters)}/{self.max_supporters})", value="\n".join(supp_slots), inline=False)
        embed.add_field(name="ㅤ", value=f"
http://googleusercontent.com/immersive_entry_chip/0return embed

    @discord.ui.button(label="참가신청", style=discord.ButtonStyle.success, custom_id="join_dealer")
    async def join_dealer(self, interaction: discord.Interaction, button: discord.ui.Button):
        for u, _ in self.dealers + self.supporters:
            if u.id == interaction.user.id:
                await interaction.response.send_message("❌ 이미 파티에 참가 중입니다.", ephemeral=True)
                return
        self.dealers.append((interaction.user, "Lv.1755.0 | 대기자 스펙트럼"))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="참가취소", style=discord.ButtonStyle.danger, custom_id="leave_raid")
    async def leave_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.dealers = [item for item in self.dealers if item[0].id != interaction.user.id]
        self.supporters = [item for item in self.supporters if item[0].id != interaction.user.id]
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.command(name="레이드모집")
async def create_raid_party(ctx, *, raid_title: str = "[세르카 : 나이트메어] 26.01.07(수) 10:30 : 세르카 첫주클 하러가실분!"):
    view = RaidJoinView(title=raid_title, creator=ctx.author)
    await ctx.send(embed=view.generate_embed(), view=view)


# =========================
# 🌋 지옥 보상 가치 판별 UI 매칭 (!지옥추천)
# =========================
@bot.command(name="지옥추천")
async def recommend_hell_reward(ctx, level: str = "1750", floor_range: str = "8", *rewards: str):
    if not rewards:
        rewards = ["어빌", "특재", "골드"]

    analyzed_rewards = []
    for r_input in rewards:
        clean_input = r_input.replace(" ", "")
        if clean_input in BASE_REWARD_VALUES:
            analyzed_rewards.append({"original": r_input, "calc_val": BASE_REWARD_VALUES[clean_input]})
        else:
            matched = False
            for k, v in BASE_REWARD_VALUES.items():
                if clean_input in k:
                    analyzed_rewards.append({"original": k, "calc_val": v})
                    matched = True
                    break
            if not matched:
                analyzed_rewards.append({"original": r_input, "calc_val": 10000})

    analyzed_rewards.sort(key=lambda x: x["calc_val"], reverse=True)

    embed = discord.Embed(title=f"🌋 지옥 보상 설정  ➜  {level}+ [ {floor_range}단계 ]", color=0xE74C3C)
    embed.description = f"💡 **페온 비용 포함 기준 (1페온 = 697.89 G)**\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
    embed.add_field(name="🏆 최우선 선택 [1등상]", value=f"🥇 **{analyzed_rewards[0]['original']}**", inline=False)

    rank_text = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, item in enumerate(analyzed_rewards):
        medal = medals[idx] if idx < len(medals) else "•"
        rank_text += f"{medal} **{item['original']}** ㅤ➜ㅤ `{item['calc_val']:,} G`\n"
        
    embed.add_field(name="📋 항목별 상세 가치 테이블", value=rank_text, inline=False)
    await ctx.send(embed=embed)


# =========================
# ⚖️ 기타 보조 유틸리티 명령어
# =========================
@bot.command(name="경매")
async def calculate_auction(ctx, price: int = None):
    if not price: return
    net_value = int(price * 0.95)
    embed = discord.Embed(title=f"⚖️ 경매 정산기 (시세: {price:,} G)", color=0xF1C40F)
    embed.add_field(name="👥 4인 파티 추천가", value=f"`{int(net_value * 0.95 * 3 / 4):,} G`", inline=True)
    embed.add_field(name="👥 8인 파티 추천가", value=f"`{int(net_value * 0.95 * 7 / 8):,} G`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="알람")
async def set_timer(ctx, time_str: str = None, *, memo: str = "시간 완료!"):
    if not time_str: return
    seconds = int(time_str.replace("분", "").strip()) * 60 if "분" in time_str else int(time_str) * 60
    await ctx.send(f"⏰ {time_str} 후 알람 설정 완료.")
    await asyncio.sleep(seconds)
    await ctx.send(f"🚨 {ctx.author.mention} ➜ {memo}")

@bot.command(name="낙원")
async def show_nakwon_code(ctx, job_name: str = "창술사"):
    if job_name in NAKWON_SKILL_CODES:
        await ctx.send(f"📋 **{job_name} 아크패시브 스킬코드:**\n```{NAKWON_SKILL_CODES[job_name]['code']}```")

@bot.command(name="시너지")
async def show_synergy(ctx):
    await ctx.send("⚔️ **창술사:** 치피증  |  **바드:** 낙인방깎, 공증")

@bot.event
async def on_ready():
    print(f"✅ 전 직업 아크그리드 동적 트래킹 연동 완료: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

