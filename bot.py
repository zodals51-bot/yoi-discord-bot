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


def get_character_profile(character_name):
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

        return r.json()
    except Exception as e:
        print("프로필 API 오류:", e)
        return None


# =========================
# 🔍 [수정본] 전투력 저격 전용 명령어
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return

    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 데이터를 가져오는 중...")
    
    profile = get_character_profile(character_name)
    if not profile:
        await status_msg.edit(content="❌ 캐릭터 정보를 가져오지 못했습니다. 캐릭터명이나 API 키를 확인해 주세요.")
        return

    try:
        char_name = profile.get("CharacterName", character_name)
        char_class = profile.get("CharacterClassName", "알 수 없음")
        title = profile.get("Title") or "없음"
        guild_name = profile.get("GuildName") or "없음"
        guild_rank = profile.get("GuildMemberGrade") or ""
        
        # 아이템 레벨 정제
        raw_item_lvl = profile.get("ItemMaxLevel") or profile.get("ItemAvgLevel") or "0"
        item_lvl = str(raw_item_lvl).replace(",", "")
        
        exp_lvl = profile.get("CharacterLevel", "0")
        exp_exp = profile.get("ExpeditionLevel", "0")
        
        # 🔥 [전투력 강제 정밀 탐색 엔진]
        total_power = "정보 없음"
        stats_list = profile.get("Stats") or []
        
        for stat in stats_list:
            stat_type = str(stat.get("Type", "")).strip()
            stat_val = str(stat.get("Value", "")).strip()
            
            # 명칭에 '전투력'이 들어가거나, 기존 세팅의 '공격력/생명력' 외에 값이 비정상적으로 큰 항목(백만 단위 이상)을 필터링
            if "전투력" in stat_type or stat_type == "전투력":
                # 내부 특수문자, 문자, 공백 싹 다 지우고 오직 숫자와 소수점만 남김
                clean_val = re.sub(r'[^\d.]', '', stat_val)
                if clean_val:
                    try:
                        # 소수점이 있을 경우를 대비해 float 변환 후 정수화 및 3자리 콤마 표시
                        total_power = f"{int(float(clean_val)):,}"
                    except ValueError:
                        total_power = stat_val  # 변환 실패시 공홈 문자열 그대로 노출
                break

        # 디스코드 임베드 카드 구성
        embed = discord.Embed(
            title=f"🛡️ {char_name} ({char_class} / {title})",
            color=0x2B2D31
        )
        
        if profile.get("CharacterImage"):
            embed.set_thumbnail(url=profile["CharacterImage"])

        embed.add_field(name="🏰 소속 길드", value=f"`{guild_name}` {guild_rank}", inline=True)
        embed.add_field(name="✨ 원정대 레벨", value=f"Lv.{exp_exp}", inline=True)
        embed.add_field(name="⚔️ 전투 레벨", value=f"Lv.{exp_lvl}", inline=True)
        
        embed.add_field(name="💎 아이템 레벨", value=f"**{item_lvl}**", inline=True)
        embed.add_field(name="🔥 전투력", value=f"**{total_power}**", inline=True)
        embed.add_field(name="ㅤ", value="ㅤ", inline=True)

        await status_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        print("명령어 내부 처리 오류:", e)
        await status_msg.edit(content="❌ 데이터 파싱 중 오류가 발생했습니다.")


# =========================
# 기존 기능 유지 (인증패널 및 큐브)
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

class CubeCalculatorModal(discord.ui.Modal, title="🎲 2인 다캐릭 통합 큐브 정산"):
    my_tickets = discord.ui.TextInput(label="내 모든 캐릭터 티켓 현황", style=discord.TextStyle.long, required=True)
    partner_tickets = discord.ui.TextInput(label="상대방 모든 캐릭터 티켓 현황", style=discord.TextStyle.long, required=True)
    def parse_and_sum_tickets(self, text):
        total = {4: 0, 3: 0, 2: 0, 1: 0}
        matches = re.findall(r'([1-4])[^\d]*(\d+)', text)
        for stage, count in matches: total[int(stage)] += int(count)
        return total
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        me = self.parse_and_sum_tickets(self.my_tickets.value)
        partner = self.parse_and_sum_tickets(self.partner_tickets.value)
        embed = discord.Embed(title="📊 2인 다캐릭 통합 큐브 정산 결과", color=0x00FFFF)
        for stage in [4, 3, 2, 1]:
            if me[stage] == 0 and partner[stage] == 0: continue
            txt = f"나 [{me[stage]}장] vs 상대방 [{partner[stage]}장]\n"
            c_triples = min(me[stage]//3, partner[stage]//3)
            if c_triples > 0: txt += f"➡️ 3배 녹이기 같이 **{c_triples}판**\n"
            embed.add_field(name=f"▶️ {stage}해금 큐브", value=txt, inline=False)
        await interaction.followup.send(embed=embed)

class CubeView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="큐브 정산하기", style=discord.ButtonStyle.blurple, custom_id="cube_calc_btn")
    async def cube_calc(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(CubeCalculatorModal())

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
