import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
import asyncio
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
def call_lostark_api(endpoint, character_name):
    try:
        if not LOSTARK_API_KEY: return None
        headers = {"accept": "application/json", "authorization": f"bearer {LOSTARK_API_KEY}"}
        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}/{endpoint}"
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return None
        return r.json()
    except: return None


# =========================
# 🛡️ [시즌 4 아크패시브 전용] 캐릭터 정보실 UI (!정보)
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return
        
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 아크 패시브 및 시즌 4 데이터 연동 중...")
    
    profile = call_lostark_api("profiles", character_name)
    engravings_data = call_lostark_api("engravings", character_name)
    equipment = call_lostark_api("equipment", character_name)
    arkpassive_data = call_lostark_api("arkpassive", character_name) # 🌟 아크패시브 전용 추가
    
    if not profile:
        await status_msg.delete()
        await ctx.send(f"❌ **{character_name}** 캐릭터 정보를 찾을 수 없거나 API 점검 중입니다.")
        return

    # 1. 기본 프로필 정보 추출
    char_name = profile.get("CharacterName", character_name)
    char_class = profile.get("CharacterClassName", "알 수 없음")
    server_name = profile.get("ServerName", "알 수 없음")
    title = profile.get("Title") or "칭호 없음"
    guild_name = profile.get("GuildName") or "없음"
    
    item_lvl = str(profile.get("ItemAvgLevel", "0"))
    exp_exp = str(profile.get("ExpeditionLevel", "0"))
    exp_lvl = str(profile.get("CharacterLevel", "0"))
    
    # 2. 전투력 / 공격력 파싱 보정 (모든 스탯 완전 스캔)
    total_power = "0"
    attack_power = "0"
    stats_list = profile.get("Stats") or []
    
    for stat in stats_list:
        s_type = str(stat.get("Type", ""))
        s_value = str(stat.get("Value", "0"))
        
        if "공격력" in s_type and "아군" not in s_type:
            clean_val = re.sub(r'[^\d]', '', s_value)
            if clean_val.isdigit(): attack_power = f"{int(clean_val):,}"
        elif "전투력" in s_type:
            clean_val = re.sub(r'[^\d]', '', s_value)
            if clean_val.isdigit(): total_power = f"{int(clean_val):,}"

    # 3. 🌟 아크 패시브 전용 엔드포인트 연동 (아크 그리드 완벽 반영)
    grid_nodes = []
    points_info = []
    
    if arkpassive_data and arkpassive_data.get("IsAvailable") is True:
        # 진화, 깨달음, 도약 포인트 요약 추출
        points = arkpassive_data.get("Points", [])
        for p in points:
            p_name = p.get("Name", "")
            p_val = p.get("Value", 0)
            points_info.append(f"{p_name} {p_val}P")
            
        # 활성화된 아크 그리드 노드명 선별
        conditions = arkpassive_data.get("Conditions", [])
        for cond in conditions:
            c_name = cond.get("Name", "")
            # 트리거된 노드 텍스트 확보
            if c_name:
                grid_nodes.append(f"• {c_name}")
    
    # 만약 아크패시브 데이터가 안 잡혔을 때의 예외 처리
    if not grid_nodes:
        grid_nodes = ["• 활성화된 아크 그리드 노드가 없습니다 (미개방)."]
    if points_info:
        ark_passive_status = " | ".join(points_info)
    else:
        ark_passive_status = "아크 패시브 비활성화 상태"

    # 4. 무기 및 방어구 세트 이름 정밀 추출
    weapon_name = "장비 정보 없음"
    armor_set_name = "장비 정보 없음"
    
    if equipment:
        for item in equipment:
            i_type = item.get("Type", "")
            raw_name = item.get("Name", "")
            clean_name = re.sub(r'\[.*?\]|\+\d+\s+', '', raw_name).strip()
            
            if i_type == "무기":
                weapon_name = clean_name
            elif i_type in ["투구", "상의", "하의", "장갑", "어깨"] and armor_set_name == "장비 정보 없음":
                armor_set_name = re.sub(r'투구|상의|하의|장갑|어깨', '', clean_name).strip()

    # 5. 🌟 각인서 정보 실시간 파싱 보정
    # 아크 패시브 활성화 시 engravings 혹은 arkpassive 내 각인 정보 데이터 매칭
    eng_text = ""
    if engravings_data and "Effects" in engravings_data:
        eng_list = engravings_data["Effects"] or []
        for eng in eng_list:
            e_name = eng.get("Name", "")
            if e_name:
                eng_text += f"• 🟥 **{e_name}**\n"
                
    # 만약 기존 각인이 비어있다면 아크패시브 내에 커스텀 각인이 있는지 재확인
    if not eng_text and arkpassive_data:
        ark_engravings = arkpassive_data.get("Effects", []) # 아크패시브 내부 각인 효과 대치
        for ae in ark_engravings:
            ae_name = ae.get("Name", "")
            if ae_name:
                eng_text += f"• 🟥 **{ae_name}**\n"

    if not eng_text:
        eng_text = "• ⬜ 활성화된 각인 시스템 없음"

    # UI 조립 및 출력
    embed = discord.Embed(
        title=f"🎭 {server_name}  |  {char_name} ㅤ", 
        description=f"**{char_class}** 세팅 정보 실시간 동기화\n칭호: `{title}` ㅤ|ㅤ 길드: `{guild_name}`",
        color=0x1E1F22
    )
    if profile.get("CharacterImage"): 
        embed.set_thumbnail(url=profile["CharacterImage"])

    # 상단 정보 블록
    embed.add_field(name="📋 기본 정보", value=f"• 아이템 Lv: `{item_lvl}`\n• 원정대 Lv: `{exp_exp}`\n• 전투 Lv: `Lv.{exp_lvl}`", inline=True)
    embed.add_field(name="🔥 핵심 스탯", value=f"• 전투력: **{total_power}**\n• 공격력: `{attack_power}`", inline=True)
    embed.add_field(name="✨ 장비 세팅", value=f"• 무기: `{weapon_name}`\n• 방어구 세트: `{armor_set_name}`", inline=True)

    # 💠 [진짜 동적 데이터] 아크 그리드 분배 현황
    embed.add_field(name=f"💠 {char_name} 아크 그리드 현황", value=f"```md\n" + "\n".join(grid_nodes) + "```", inline=False)

    # ⚡ 아크 패시브 포인트 요약 정보
    embed.add_field(name="⚡ 아크 패시브 가동 스펙", value=f"```md\n[현재 분배 스펙]\n➜ {ark_passive_status}```", inline=False)

    # 하단 각인서
    embed.add_field(name="🔸 활성화 각인 시스템", value=eng_text, inline=True)

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
        self.dealers = [(creator, "공격대장 👑")]
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
        return embed

    @discord.ui.button(label="참가신청", style=discord.ButtonStyle.success, custom_id="join_dealer")
    async def join_dealer(self, interaction: discord.Interaction, button: discord.ui.Button):
        for u, _ in self.dealers + self.supporters:
            if u.id == interaction.user.id:
                await interaction.response.send_message("❌ 이미 파티에 참가 중입니다.", ephemeral=True)
                return
        self.dealers.append((interaction.user, "공격대 참가자"))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="참가취소", style=discord.ButtonStyle.danger, custom_id="leave_raid")
    async def leave_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.dealers = [item for item in self.dealers if item[0].id != interaction.user.id]
        self.supporters = [item for item in self.supporters if item[0].id != interaction.user.id]
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.command(name="레이드모집")
async def create_raid_party(ctx, *, raid_title: str = "[레이드] 공격대 모집"):
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

@bot.event
async def on_ready():
    print(f"✅ 시즌 4 아크패시브(arkpassive) 정밀 동기화 완료: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
