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
# 🎲 [개편] 캐릭별 3배/1배 최적 동선 계산기
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 캐릭터별 큐브 매칭 정산"):
    my_tickets = discord.ui.TextInput(
        label="내 캐릭별 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n환수사 4해금 5\n기상 4해금 2",
        style=discord.TextStyle.long, required=True
    )
    partner_tickets = discord.ui.TextInput(
        label="상대방 캐릭별 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n죽창 4해금 4\n슬레이어 4해금 3",
        style=discord.TextStyle.long, required=True
    )

    def parse_tickets_by_char(self, text):
        # 캐릭터별로 해금 단계와 장수를 파싱하는 로직
        # 딕셔너리 구조: { 해금단계: { 캐릭터명: 장수 } }
        data = {4: {}, 3: {}, 2: {}, 1: {}}
        lines = text.strip().split('\n')
        for line in lines:
            if not line.strip(): continue
            # 정규식으로 숫자(해금단계), 뒤에 오는 숫자(티켓수) 추출
            match = re.search(r'([1-4])[^\d]*(\d+)', line)
            if match:
                stage = int(match.group(1))
                count = int(match.group(2))
                # 숫자들을 제외한 앞부분 문자열을 캐릭터 이름으로 인식 (공백 제거)
                char_name = line.split(match.group(0))[0].strip()
                if not char_name:
                    char_name = f"캐릭_{stage}"
                data[stage][char_name] = data[stage].get(char_name, 0) + count
        return data

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        me = self.parse_tickets_by_char(self.my_tickets.value)
        partner = self.parse_tickets_by_char(self.partner_tickets.value)

        embed = discord.Embed(title="📊 캐릭터별 최적 큐브 동선 설계", color=0x00FFFF)
        embed.description = "두 분의 캐릭터별 보유량을 매칭한 가장 깔끔한 소모 순서입니다.\n"
        
        has_data = False

        for stage in [4, 3, 2, 1]:
            my_chars = {k: v for k, v in me[stage].items() if v > 0}
            partner_chars = {k: v for k, v in partner[stage].items() if v > 0}

            if not my_chars and not partner_chars:
                continue

            has_data = True
            stage_text = ""

            # 1단계: 3배 소모 최적 매칭 (내가 3장 이상, 상대가 3장 이상 있을 때 캐릭 매칭)
            stage_text += "**🔹 [3배 소모 조합]**\n"
            triple_found = False
            
            for m_char in list(my_chars.keys()):
                for p_char in list(partner_chars.keys()):
                    if my_chars[m_char] >= 3 and partner_chars[p_char] >= 3:
                        # 두 캐릭이 동시에 돌 수 있는 최대 3배 판수 계산
                        m_triples = my_chars[m_char] // 3
                        p_triples = partner_chars[p_char] // 3
                        pan = min(m_triples, p_triples)
                        
                        if pan > 0:
                            stage_text += f"➔ 나의 **[{m_char}]** ⚔️ 상대 **[{p_char}]** ➜ **3배로 {pan}판** 같이 가기\n"
                            my_chars[m_char] -= pan * 3
                            partner_chars[p_char] -= pan * 3
                            triple_found = True
            
            if not triple_found:
                stage_text += "➔ 캐릭터 간 3장씩 딱 맞아떨어지는 3배 조합이 없습니다.\n"

            # 2단계: 1배 소모 및 잔여 티켓 믹스 매칭
            stage_text += "\n**🔸 [1배 소모 및 잔여 믹스]**\n"
            single_found = False
            
            # 남은 티켓이 있는 캐릭터들 필터링
            my_remains = {k: v for k, v in my_chars.items() if v > 0}
            partner_remains = {k: v for k, v in partner_chars.items() if v > 0}

            for m_char in list(my_remains.keys()):
                for p_char in list(partner_remains.keys()):
                    if my_remains[m_char] > 0 and partner_remains[p_char] > 0:
                        pan = min(my_remains[m_char], partner_remains[p_char])
                        stage_text += f"➔ 나의 **[{m_char}]** ({my_remains[m_char]}장 남음) ⚔️ 상대 **[{p_char}]** ({partner_remains[p_char]}장 남음) ➜ **1배로 {pan}판** 같이 녹이기\n"
                        my_remains[m_char] -= pan
                        partner_remains[p_char] -= pan
                        single_found = True

            if not single_found and triple_found:
                # 3배로 다 털어내고 남은 자투리가 없을 때
                stage_text += "➔ 3배 조합으로 남김없이 깔끔하게 정산되었습니다!\n"
            elif not single_found and not triple_found:
                stage_text += "➔ 함께 뺄 수 있는 캐릭터 조합이 존재하지 않습니다.\n"

            embed.add_field(name=f"▶️ {stage}해금 에브니 큐브 파트너 가이드", value=stage_text + "─", inline=False)

        if not has_data:
            await interaction.followup.send("❌ 입력 양식에서 티켓 데이터를 파싱하지 못했습니다. (예: `닉네임 4해금 3장` 형식)")
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
