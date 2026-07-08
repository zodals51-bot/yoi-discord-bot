import discord
from discord.ext import commands
import requests
import config
import re

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

        try:
            await member.edit(nick=f"{info['name']}/{info['class']}")
        except Exception as e:
            print("닉네임 변경 실패:", e)

        roles_to_add = [info["class"]]
        embed_title = "✅ 인증 완료"
        embed_color = 0x57F287
        embed_description = f"**{info['name']}**님, 인증이 완료되었습니다."

        is_guild_member = info["guild"].strip() == config.GUILD_NAME.strip()

        if is_guild_member:
            roles_to_add.append(config.MEMBER_ROLE)
            print(f"📢 [길드원 확인] {info['name']} -> {config.GUILD_NAME}")
        else:
            guest_role_name = getattr(config, "GUEST_ROLE", "외부인")
            roles_to_add.append(guest_role_name)
            embed_title = "ℹ 외부인 인증 완료"
            embed_color = 0x3498DB
            current_guild = info['guild'] if info['guild'] else '없음'
            embed_description = f"**{info['name']}**님은 외부인(지인)으로 인증되었습니다.\n(조회된 길드: {current_guild})"
            print(f"📢 [외부인 확인] {info['name']} -> 소속 길드: {current_guild}")

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

        wait_role = discord.utils.get(guild.roles, name=config.WAIT_ROLE)
        if wait_role:
            try:
                await member.remove_roles(wait_role)
                print("✔ 인증대기 역할 제거 완료")
            except Exception as e:
                print("WAIT_ROLE 제거 실패:", e)

        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="캐릭터명", value=info["name"], inline=True)
        embed.add_field(name="직업", value=info["class"], inline=True)
        await interaction.followup.send(embed=embed)


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
# 🎲 [기능 고도화] 2인 다캐릭 통합 큐브 계산기 모달
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 2인 다캐릭 통합 큐브 정산"):
    my_tickets = discord.ui.TextInput(
        label="내 모든 캐릭터 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n환수사 4해금 3 / 3해금 2\n도화가 3해금 4 / 2해금 4",
        style=discord.TextStyle.long,
        required=True
    )
    partner_tickets = discord.ui.TextInput(
        label="상대방 모든 캐릭터 티켓 현황 (줄바꿈 가능)",
        placeholder="예시:\n죽창 3해금 9 / 1해금 3\n에몽 3해금 9",
        style=discord.TextStyle.long,
        required=True
    )

    # 텍스트 전체에서 해당 단계의 숫자를 모두 찾아서 누적 합산하는 함수
    def parse_and_sum_tickets(self, text):
        total = {4: 0, 3: 0, 2: 0, 1: 0}
        # 문장 전체에서 '단계/해금숫자'와 '보유수숫자' 쌍을 모두 찾아냅니다.
        matches = re.findall(r'([1-4])[^\d]*(\d+)', text)
        for stage, count in matches:
            total[int(stage)] += int(count) # 핵심: 기존 값에 계속 더해줌 (통합 누적)
        return total

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        # 여러 캐릭의 데이터를 해금별로 전수 합산
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
            
            # 단계별 통합 현황 안내
            stage_text = f"**통합 총량:** 나 [{start_me}장] vs 상대방 [{start_partner}장]\n"

            # 1. 3배 소모 계산
            me_triples = current_me // 3
            partner_triples = current_partner // 3
            common_triples = min(me_triples, partner_triples)

            if common_triples > 0:
                stage_text += f"➡️ **[3배 소모]** 캐릭 변경해가며 같이 **{common_triples}판** 진행\n"
                current_me -= common_triples * 3
                current_partner -= common_triples * 3
                stage_text += f" └ *3배 소모 후 남은 총량:* 나 [{current_me}장] / 상대방 [{current_partner}장]\n"
            else:
                stage_text += f"➡️ **[3배 소모]** 3장씩 묶어 뺄 수 있는 공통 판수가 없습니다.\n"

            # 2. 1배 믹스 소모 계산
            common_singles = min(current_me, current_partner)
            if common_singles > 0:
                stage_text += f"➡️ **[1배 믹스]** 남은 티켓으로 같이 **{common_singles}판** 녹이기\n"
                current_me -= common_singles
                current_partner -= common_singles
                stage_text += f" └ *1배 믹스 후 최종 잔여:* 나 [{current_me}장] / 상대방 [{current_partner}장]\n"

            # 3. 결론 요약
            stage_text += "✨ **추천 루틴:** "
            actions = []
            if common_triples > 0:
                actions.append(f"3배로 {common_triples}판")
            if common_singles > 0:
                actions.append(f"1배로 {common_singles}판")
            
            if actions:
                stage_text += f"**{' ➡️ '.join(actions)}**을 같이 도는 것이 가장 깔끔합니다.\n"
            else:
                stage_text += "함께 뺄 수 있는 조합이 없습니다.\n"

            # 남는 짜투리 경고
            if current_me > 0 or current_partner > 0:
                stage_text += f"⚠️ *매칭 안 되고 남는 조각:* 나 [{current_me}장] / 상대방 [{current_partner}장]\n"

            if stage_text:
                embed.add_field(name=f"▶️ {stage}해금 에브니 큐브 통합 결과", value=stage_text + "─", inline=False)
                has_data = True

        if not has_data:
            await interaction.followup.send("❌ 입력 양식이 잘못되었거나 계산할 티켓 정보가 없습니다.")
            return

        await interaction.followup.send(embed=embed)


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
# 봇 시작 및 명령어
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(CubeView())
    print(f"✅ 로그인 완료: {bot.user}")


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
        description="나와 상대방의 모든 캐릭터 티켓 현황을 붙여넣으세요.\n전체 보유량을 합산하여 가장 효율적인 믹스 루틴을 짜드립니다.",
        color=0x2B2D31
    )
    await ctx.send(embed=embed, view=CubeView())


bot.run(config.DISCORD_TOKEN)
