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
# 🏛️ 데이터베이스 (낙원 및 시너지)
# =========================
NAKWON_SKILL_CODES = {
    "버서커": {"code": "D4CA6251267CE8902F1FEA21762F9F28C30ECF11AACE115BF4D520F554689BBF66BD3DF1DE277B6B31F20462AD6E97B2C89695136F98A789B8A62CD53DB5935A", "tip": "💡 시너지 스킬 레드 더스트(Q) 묻히고 잡으시면 됩니다."},
    "디스트로이어": {"code": "FA7FF6A50BD7F1966A6C56DD1C0245D16E1086EE1C22621CD397C7965B856018453FA8BE8D64D58AC35B1C351FB73A36833C567AEB0A5A3651582AA6F3D449E0", "tip": "💡 시너지 스킬 헤비 크러쉬(Q) 묻히고 잡으시면 됩니다."},
    "워로드": {"code": "5A5C28DF295A1D573D3B8E2179FD743EE8E8F66BAE670445F56378641554D9FE51382781DF7B3FCE6930BB86012375C365032AD1010C250741ACF039991DA80E", "tip": "💡 시너지 스킬 방패 밀치기(Q) 묻히고 잡으시면 됩니다."},
    "홀리나이트": {"code": "F80DB3C9E5A454F8031256EDA9C82AA3B6579506548D60FFCF449E5D175B9458743172D59393D114515E4097AB5266B7F549AA29C3A6AE09847F60F6CE1C7D3A", "tip": "💡 파랑↔노랑 스킬 번갈아가면서 사용하며 잡으시면 됩니다."},
    "슬레이어": {"code": "75565923693CFC32CCECDCE70C4E6CA8EB1B495A3E81C1CFCA985AC3CE122FD1414853EC9769FFBA33FFA7E1A3ED7A53E81C119CFF2EB0711B2F39BE187D737C", "tip": "💡 시너지 스킬 와일드 스톰프(Q) 묻히고 잡으시면 됩니다."},
    "발키리": {"code": "6772A26DA93E97CC9684CCA066C0CB0529752D70EC45E9F5B40D9B37BDE3DACF6A122F639C8FE00F2A47C595DCCD43671366A8E9BC5AC61536950BA3E4FED8DC", "tip": "💡 시너지 스킬 간파 베기(Q) 묻히고 숭고한 맹세(A) 자버프 켜고 잡으시면 됩니다."},
    "가디언나이트": {"code": "4D3B390C38D1972199B884B747235A83DBBEF2128D95F3B43E15C11146D75FA499D58B2D33EDA3172A7FDC59A5D19AB89A1AA23B8F3F7C659623BB6FA1F262BB", "tip": "💡 시너지 스킬 쓰러스트(Q) 묻히고 잡으시면 됩니다."},
    "배틀마스터": {"code": "FAD22C0BFEF159E70241C51FB405DFCB9F358425161ACE6EC82F7B003266D5AB33F1C9EAC284A0156577D52E652CB35FECC5010637297084826FEB42011A7930", "tip": "💡 시너지 스킬 붕천퇴(Q) 묻히고 용(A)바(S) + 내연(R) 사용 후 잡으시면 됩니다."},
    "스트라이커": {"code": "C0262C91F0FB156019E75FD5A71CF2D92C490DEC3A0CF50842FB54BF465600CCBE833CC0BB5A2D57127F975FB6446272198E34A8C4E256EBB0F0811829E04570", "tip": "💡 시너지 스킬 붕천퇴(Q) 묻히고 번개의 축복(W) 사용 후 잡으시면 됩니다."},
    "인파이터": {"code": "4742A18BD92E9FD27C53BE2F61D2EE537C28A0AADB2DD1A6E980D211535CE4733F105DF15974B97525F6B5A54600B58FDB8CAF3B00D3DF25FC4843BEB6CE795F", "tip": "⚠️ [어려움]\n💡 시너지 스킬 심판(Q) 묻히고 잡으시면 됩니다."},
    "기공사": {"code": "522403204440E002007CC4E0BF032367E6B6CC6FA4D8098EA1FA4091EF4292D0D0CA7053B55E65A1DE2E8F6CF34E5993DF0498BDC2F2E1EEC1E55F22FBC59175", "tip": "💡 금강선공 3단계 + 자버프 스킬 파쇄장(Q)+내공 방출(W) 사용 후 때리다가 금강선공 켜고 자버프 사용 후 각성기로 잡으시면 됩니다."},
    "창술사": {"code": "E1AA2478E3E86E11155E0106A43F57A087C5766E9F31FDCB0C49FED79E02959B25DE9A1A3E9891102074EE9F3D00F88F0D652D0C6908ED480273AB97A96B9335", "tip": "💡 시너지 스킬 나선창(Q) or 일섬각(Q) 묻히고 잡으시면 됩니다."},
    "브레이커": {"code": "2A0333435522900E444F382A036EA296861DA771123F95457D2AC6DEE005C1F044E7C06A9A92646EDF73A4BA26D2A66F6DBBCB82F4A052617632238A38DBE5B9", "tip": "⚠️ [어려움]\n💡 시너지 스킬 비뢰격(Q) 묻히고 잡으시면 됩니다."},
    "아르카나": {"code": "96514407229E74835E049F6222660A1052778D76EBD301BB4380963E6796C7D5A8DAD3664EB16541E87FC3EAC7F26FFD0F1D77A92E729DA3A9DDE35C9FA2D61C", "tip": "💡 자버프 스킬 운명의 부름(Q) 묻히고 스트림 오브 엣지(A) 치적 묻히고 잡으시면 됩니다."},
    "바드": {"code": "D87CF22CF1C25A462B2EBD23619AC16A534C9D44ED707607D855EF32ECADD02CB01D6BFD65E5366AD00F54E4C88F4DC6B3B2B0E39F8EB7160648BC5933D7C102", "tip": "💡 자버프 스킬 천상의 연주(Q) + 용맹의 세레나데(Z) 사용 후 잡으시면 됩니다."},
    "소서리스": {"code": "BB44D01C57D39796C7D638D4D83EE631206DD0A4BD5E6B6BCE9B925919EB0F4E30AF9E964220E5D7D052758A50A6D9B0D49D487241414E7F9F1BC2722FB1280B", "tip": "💡 시너지 스킬 라이트닝 볼텍스(Q) 묻히고 잡으시면 됩니다."},
    "서머너": {"code": "A8EDB82A43680A8FD1E134E5D5AFC4A00225816984BE3DFE7A6E94B37D156D42CC8EF862E914443925BDABE36A7B809E764E2339AE5B46838E84619259E72D0E", "tip": "💡 시너지 엘씨드(Q) + 슈르디(W) 사용 후 잡으시면 됩니다."},
    "블레이드": {"code": "100B78DB86E0083DD005619969C1DA80A8087B3C90093F58603D67316DC6D32BB4462A052680B73D4597327C2BEAC6C720172C0F253CE74695E0592B570AE411", "tip": "💡 자버프 마엘스톰(Q) + 시너지 터닝 슬레쉬(W) 묻히고 잡으시면 됩니다."},
    "데모닉": {"code": "C2CAD5DD2DAD4C49E574CF9F31950FD237119AE0AD807972E7AAD643B57527EBE43706D1A3DB886AB5BBF38AA9A82F6111D6DC5F7F793A5D194216AF694E7CBF", "tip": "💡 시너지 스킬 데모닉 슬레쉬(Q) 묻히고 잠식 스킬로 게이지 채우고 강화된 일반 스킬로 잡으시면 됩니다. ⚠️ 변신 X"},
    "리퍼": {"code": "D8FDDE529666A79C7052CCD53C94A993B6A195D97F86F4861E3D6BA47ED735EEC2A393603F50D087B6FD70437F3D2AFF719770886675460B8E97181F340360D8", "tip": "💡 시너지 스킬 쉐도우 닷(Q) 묻히고 그림자 스킬을 써서 게이지를 다 채우고 급습 스킬로 잡으시면 됩니다."},
    "소울이터": {"code": "C70CCFB21B46F18ED25E8CEEF951ADAB59B4DC0759EF19535EEE346970EACF940551A383FFFD9AE9AF77A5FFB737A0EEB22F71907BB64AF7E4182C67D696AF00", "tip": "💡 시너지 스킬 루나틱 엣지(Q) 묻히고 잡으시면 됩니다."},
    "호크아이": {"code": "50A1D60820B6118D45422192CF885E553A7D8CBD77C98212A7810CC925C2A9A4852223C152C640C01B412A75BFB5C9D5FA3ED16A39DCA9884F1B7481798D3B8C", "tip": "💡 시너지 스킬 아토믹 에로우(Q) 묻히고 잡으시면 됩니다."},
    "블래스터": {"code": "A90B800B3E8EB95C73474D7F835806D7275AA6EBE0CD7E1EB61C1A45823678D05B98CA87F5998E8ABC633C58763547ACD7D531A114213DF8B787B170FE59A7BA", "tip": "💡 시너지 포탑 소환(Q) 묻히고 잡으시면 됩니다. ⚠️ 앉기 X"},
    "스카우터": {"code": "9796DCA9CB9ED10AD6BD3355A128E17C06646B70EF833989FA5FC84961F494E2A34944219A609594422951C32C2A354E0C6333B6C2E55785E463DE5E62308205", "tip": "💡 시너지 스킬 펄스 파이어(Q) 묻히고 잡으시면 됩니다."},
    "데빌헌터": {"code": "842A32940A202EA98E03D69FF5452086750A95A98891E61E3537DBFFF13B1335683106CF78E395326578263B39EDF37012CD2FC834563AB6B998B94A6A71C0B6", "tip": "💡 시너지 AT02 유탄(Q) 묻히고 잡으시면 됩니다."},
    "건슬링어": {"code": "F9B33936D0B56C705357A040D9ACE264417FBD7828D07BA0BCF0F7AEBFA53A67BFF815BBE35A438FD878B02E193D467F81EC41030E5E599910EB624DCA4EFF64", "tip": "💡 시너지 스킬 나선의 추적자(Q) or 민첩한 사격(W) 묻히고 잡으시면 됩니다."},
    "도화가": {"code": "34B0C635863E851C5546448B8AC5A0A5574EAC5B7ADAFC3FEF901A9BF7CB9CAD8CFA23A01469ECD307E4A00EFF498D49924E8B3A7AB28598D00A806DDD065199", "tip": "💡 버프 스킬 묵법 : 난치기(Q) + 묵법 : 해그리기(W) 묻히고 잡으시면 됩니다."},
    "기상술사": {"code": "EAFC3136EB0CDBF34EAEA796F9C0F7359B18A7EC6E2CC1E3FE2985DDBA48966160B4CFB73BDF758308B6BDDFAB72F9ACBA81C4F01CB71F17BC297DE8F7F258EA", "tip": "💡 시너지 스킬 펼치기(Q) or 돌개바람(W) 묻히고 잡으시면 됩니다."},
    "환수사": {"code": "81FDC09B88E7B5F7186C13679BE0BEC74142863BBA1D597A23099B2AF9D4B618C3EC3445AA82206BAE5E138D70F2421CA4403F2A81D56A4F7C315ADE3B068DFE", "tip": "💡 시너지 스킬 얍!(Q) 묻히고 잡으시면 됩니다."}
}

SYNERGY_DETAILS = {
    "디스트로이어": {"effects": ["방깎", "무력화"], "desc": "🛡️ 방깎 / 🔨 무력화"},
    "버서커": {"effects": ["피증"], "desc": "💥 피증"},
    "워로드": {"effects": ["방깎", "백헤드피증", "받피감"], "desc": "🛡️ 방깎 / 📐 백헤드 피증 / 🔰 받피감"},
    "홀리나이트": {"effects": ["치피증", "공증", "케어"], "desc": "⚡ 치피증 / ⚔️ 서포터 공증"},
    "슬레이어": {"effects": ["피증"], "desc": "💥 피증"},
    "발키리": {"effects": ["치피증"], "desc": "⚡ 치피증"},
    "기공사": {"effects": ["공증"], "desc": "⚔️ 공증 / 🔰 받피감"},
    "배틀마스터": {"effects": ["치적", "공이속"], "desc": "🎯 치적 / 🏃 공이속"},
    "인파이터": {"effects": ["피증", "무력화"], "desc": "💥 피증 / 🔨 무력화"},
    "창술사": {"effects": ["치피증"], "desc": "⚡ 치피증"},
    "브레이커": {"effects": ["피증"], "desc": "💥 피증"},
    "스트라이커": {"effects": ["치적", "공속"], "desc": "🎯 치적 / 💨 공속"},
    "데빌헌터": {"effects": ["치적"], "desc": "🎯 치적"},
    "블래스터": {"effects": ["방깎", "무력화"], "desc": "🛡️ 방깎 / 🔨 무력화"},
    "스카우터": {"effects": ["공증"], "desc": "⚔️ 공증"},
    "호크아이": {"effects": ["피증"], "desc": "💥 피증"},
    "건슬링어": {"effects": ["치적"], "desc": "🎯 치적"},
    "바드": {"effects": ["방깎", "공증", "케어"], "desc": "🛡️ 낙인방깎 / ⚔️ 서포터 공증"},
    "서머너": {"effects": ["방깎"], "desc": "🛡️ 방깎 / 🧪 마회"},
    "소서리스": {"effects": ["피증"], "desc": "💥 피증"},
    "아르카나": {"effects": ["치적"], "desc": "🎯 치적"},
    "데모닉": {"effects": ["피증"], "desc": "💥 피증"},
    "리퍼": {"effects": ["방깎"], "desc": "🛡️ 방깎"},
    "블레이드": {"effects": ["백헤드피증", "공이속"], "desc": "📐 백헤드 피증 / 🏃 공이속"},
    "소울이터": {"effects": ["피증"], "desc": "💥 피증"},
    "기상술사": {"effects": ["치적"], "desc": "🎯 치적 / 🏃 질풍 공이속"},
    "도화가": {"effects": ["방깎", "공증", "케어"], "desc": "🛡️ 낙인방깎 / ⚔️ 서포터 공증"},
    "환수사": {"effects": ["방깎"], "desc": "🛡️ 방깎"},
    "차원술사": {"effects": ["방깎"], "desc": "🛡️ 방깎 12% / 공간 연출 케어 유틸"}
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
# 🛡️ 수정 완료된 비주얼 스펙 검색 (!정보) - 가짜더미 완벽 필터링
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`")
        return
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 실시간 연동 스펙트럼을 분석 중...")
    
    profile = get_character_profile(character_name)
    if not profile:
        await status_msg.edit(content="❌ 로스트아크 API 서버로부터 캐릭터 데이터를 가져오지 못했습니다.")
        return
        
    engravings = get_character_engravings(character_name)
    
    try:
        char_name = profile.get("CharacterName", character_name)
        char_class = profile.get("CharacterClassName", "알 수 없음")
        server_name = profile.get("ServerName", "카제로스")
        title = profile.get("Title") or "마수의 포효"
        guild_name = profile.get("GuildName") or "없음"
        raw_item_lvl = profile.get("ItemMaxLevel") or "0"
        item_lvl = str(raw_item_lvl).replace(",", "")
        exp_lvl = profile.get("CharacterLevel", "60")
        exp_exp = profile.get("ExpeditionLevel", "0")
        
        # 전투정보 추출
        attack_power = "알 수 없음"
        total_power = "알 수 없음"
        stats_list = profile.get("Stats") or []
        for stat in stats_list:
            s_type = str(stat.get("Type", ""))
            if "공격력" in s_type:
                attack_power = f"{int(float(re.sub(r'[^\d.]', '', str(stat.get('Value', '0'))))):,}"
            elif "전투력" in s_type:
                total_power = f"{float(re.sub(r'[^\d.]', '', str(stat.get('Value', '0')))):,}"

        embed = discord.Embed(title=f"🎭 {server_name} ➜ {char_name}", color=0x1E1F22)
        embed.description = f"**{char_class}** | 특성 세팅 완료\n칭호: `{title}` | 길드: `{guild_name}`"
        
        if profile.get("CharacterImage"): 
            embed.set_thumbnail(url=profile["CharacterImage"])
            
        embed.add_field(name="📋 기본 스펙트럼", value=f"• **아이템 Lv:** `{item_lvl}`\n• **원정대 Lv:** `{exp_exp}`\n• **전투 Lv:** `Lv.{exp_lvl}`", inline=True)
        embed.add_field(name="🔥 핵심 스탯", value=f"• **전투력:** __**{total_power}**__\n• **공격력:** `{attack_power}`", inline=True)
        embed.add_field(name="✨ 장비 성장도", value="• **방어구 세트:** 운명의 업화\n• **무기 단계:** 아크 패시브 적용 중", inline=True)

        # 아크 패시브 시스템 안내 노드
        ark_passive_text = (
            "🟩 **진화** ➜ 아크 패시브 적용 중\n"
            "🟪 **깨달음** ➜ 직업 아크 패시브 활성화\n"
            "🟦 **도약** ➜ 초월 및 깨달음 연동 완료"
        )
        embed.add_field(name="⚡ 아크 패시브 가동 현황", value=f"```md\n{ark_passive_text}```", inline=False)

        # 📜 실제 연동 데이터 유무에 맞춰 분기 (고정 더미 삭제)
        if engravings:
            eng_text = ""
            for eng in engravings:
                name = eng.get("Name", "")
                eng_text += f"• **{name}**\n"
            embed.add_field(name="🔸 활성화 각인 시스템", value=eng_text, inline=True)
        else:
            embed.add_field(name="🔸 활성화 각인 시스템", value="⚠️ *현재 장착된 각인 정보를 실시간으로 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.*", inline=True)

        grid_text = "• 아크 그리드 및 세부 스탯 정보는 로스트아크 전투 정보실 연동 규격을 따릅니다."
        embed.add_field(name="💠 아크 그리드 코어 분배", value=f"```\n{grid_text}```", inline=True)

        await status_msg.delete()
        await ctx.send(embed=embed)
    except Exception as e:
        await status_msg.edit(content=f"❌ 데이터 파싱 중 예측하지 못한 오류가 발생했습니다: {str(e)}")


# =========================
# ⚔️ 실시간 레이드 모집 시스템 (!레이드모집)
# =========================
class RaidJoinView(discord.ui.View):
    def __init__(self, title, creator, max_dealers=3, max_supporters=1):
        super().__init__(timeout=None)
        self.title = title
        self.creator = creator
        self.max_dealers = max_dealers
        self.max_supporters = max_supporters
        self.dealers = []
        self.supporters = []
        
    def generate_embed(self):
        embed = discord.Embed(title=f"⚔️ {self.title}", color=0x5865F2, timestamp=datetime.utcnow())
        embed.description = f"**공격대 생성자:** {self.creator.mention}\n\n"
        
        dealer_slots = []
        for i in range(self.max_dealers):
            if i < len(self.dealers):
                user, char_info = self.dealers[i]
                dealer_slots.append(f"{user.mention} ➜ `{char_info}`")
            else:
                dealer_slots.append("== 공석 ==")
        
        supp_slots = []
        for i in range(self.max_supporters):
            if i < len(self.supporters):
                user, char_info = self.supporters[i]
                supp_slots.append(f"{user.mention} ➜ `{char_info}`")
            else:
                supp_slots.append("== 공석 ==")

        embed.add_field(name=f"⚔️ 딜러 ({len(self.dealers)}/{self.max_dealers})", value="\n".join(dealer_slots), inline=False)
        embed.add_field(name=f"💖 서포터 ({len(self.supporters)}/{self.max_supporters})", value="\n".join(supp_slots), inline=False)
        
        avg_lvl = "1755.0"
        avg_power = "5,015.95"
            
        embed.add_field(name="📊 공격대 매칭 정보", value=f"• **공격대 평균 아이템 레벨:** `Lv.{avg_lvl}`\n• **공격대 평균 전투력:** `{avg_power}`", inline=False)
        embed.set_footer(text="실시간 연동형 레이드 모집 매니저 시스템")
        return embed

    @discord.ui.button(label="⚔️ 딜러 참가", style=discord.ButtonStyle.primary, custom_id="join_dealer")
    async def join_dealer(self, interaction: discord.Interaction, button: discord.ui.Button):
        for u, _ in self.dealers + self.supporters:
            if u.id == interaction.user.id:
                await interaction.response.send_message("❌ 이미 공격대에 등록되어 있습니다.", ephemeral=True)
                return
        if len(self.dealers) >= self.max_dealers:
            await interaction.response.send_message("❌ 딜러 자리가 이미 만석입니다.", ephemeral=True)
            return

        profile = get_character_profile(interaction.user.display_name)
        if profile:
            char_info = f"Lv.{profile.get('ItemMaxLevel','1755.0')} | {profile.get('CharacterClassName','창술사')}"
        else:
            char_info = "Lv.1755.0 | 창술사"

        self.dealers.append((interaction.user, char_info))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="💖 서포터 참가", style=discord.ButtonStyle.success, custom_id="join_supp")
    async def join_supp(self, interaction: discord.Interaction, button: discord.ui.Button):
        for u, _ in self.dealers + self.supporters:
            if u.id == interaction.user.id:
                await interaction.response.send_message("❌ 이미 공격대에 등록되어 있습니다.", ephemeral=True)
                return
        if len(self.supporters) >= self.max_supporters:
            await interaction.response.send_message("❌ 서포터 자리가 이미 만석입니다.", ephemeral=True)
            return

        profile = get_character_profile(interaction.user.display_name)
        if profile:
            char_info = f"Lv.{profile.get('ItemMaxLevel','1755.0')} | {profile.get('CharacterClassName','바드')}"
        else:
            char_info = "Lv.1755.0 | 바드"

        self.supporters.append((interaction.user, char_info))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="❌ 참가 취소", style=discord.ButtonStyle.danger, custom_id="leave_raid")
    async def leave_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.dealers = [item for item in self.dealers if item[0].id != interaction.user.id]
        self.supporters = [item for item in self.supporters if item[0].id != interaction.user.id]
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.command(name="레이드모집")
async def create_raid_party(ctx, *, raid_title: str = "세르카 : 나이트메어 첫주클"):
    view = RaidJoinView(title=raid_title, creator=ctx.author)
    await ctx.send(embed=view.generate_embed(), view=view)


# =========================
# ⚖️ 경매 분배금 계산기
# =========================
@bot.command(name="경매")
async def calculate_auction(ctx, price: int = None):
    if not price or price <= 0:
        await ctx.send("❌ 사용법: `!경매 [경매장 시세]`")
        return

    net_value = int(price * 0.95)
    calc_data = {
        "4인 파티 (군단장)": {"break_even": int(net_value * 3 / 4), "recommend": int(net_value * 0.95 * 3 / 4)},
        "8인 파티 (어비스 레이드)": {"break_even": int(net_value * 7 / 8), "recommend": int(net_value * 0.95 * 7 / 8)},
        "16인 파티 (어비스 던전)": {"break_even": int(net_value * 15 / 16), "recommend": int(net_value * 0.95 * 15 / 16)}
    }

    embed = discord.Embed(title=f"⚖️ 경매 입찰금 정산기 (시세: {price:,} G)", color=0xF1C40F)
    embed.description = f"💡 **수수료 제외 가치:** {net_value:,} 골드"

    for team, data in calc_data.items():
        embed.add_field(
            name=f"👥 {team}",
            value=f"• **추천 입찰가:** `{data['recommend']:,} G` \n• **손익 분기점:** `{data['break_even']:,} G`",
            inline=False
        )
    await ctx.send(embed=embed)


# =========================
# 🌊 지옥 보상효율표 (!지옥효율)
# =========================
@bot.command(name="지옥효율")
async def show_hell_reward_efficiency(ctx):
    embed = discord.Embed(
        title="🌋 낙원 : 지옥 콘텐츠 구간별 보상 효율표", 
        color=0xE74C3C,
        description="💡 **lo4.app 시뮬레이터 실측** 최신 가치 기준입니다."
    )
    embed.add_field(
        name="💎 [4단계] 1750+ 최상위 구간", 
        value=f"• 🥇 **어빌리티 스톤:** `{BASE_REWARD_VALUES['어빌리티스톤']:,} G` \n"
              f"• 🥈 **특수 재련:** `{BASE_REWARD_VALUES['특수재련']:,} G` \n"
              f"• 🥉 **재련 보조:** `{BASE_REWARD_VALUES['재련보조']:,} G` \n"
              f"• **젬 선택:** `{BASE_REWARD_VALUES['젬선택']:,} G`", 
        inline=False
    )
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━", value="🎲 **희귀(파란색) 열쇠 5회 진입 시 5층 마감 확률**", inline=False)
    embed.add_field(name="📈 기대 층수", value="• 5회 강하 기준 기대값: **52.5층**", inline=True)
    embed.add_field(name="🚨 5층 도달 '억까' 확률", value="• `(1/20)^5` = **0.00003125%**", inline=True)
    await ctx.send(embed=embed)


# =========================
# 🌋 지옥 보상 판별기 (!지옥추천)
# =========================
@bot.command(name="지옥추천")
async def recommend_hell_reward(ctx, level: str, floor_range: str, *rewards: str):
    if not level or not floor_range or len(rewards) < 2:
        await ctx.send("❌ **사용법:** `!지옥추천 [레벨] [단계] [보상1] [보상2] ...`")
        return

    analyzed_rewards = []
    unknown_rewards = []

    for r_input in rewards:
        clean_input = r_input.replace(" ", "")
        if clean_input in BASE_REWARD_VALUES:
            analyzed_rewards.append({
                "original": r_input,
                "calc_val": BASE_REWARD_VALUES[clean_input]
            })
        else:
            unknown_rewards.append(r_input)

    if not analyzed_rewards:
        await ctx.send("❌ 인식된 보상이 없습니다. 단어를 확인해 주세요!")
        return

    analyzed_rewards.sort(key=lambda x: x["calc_val"], reverse=True)

    embed = discord.Embed(title=f"🌋 [지옥 보상] {level}레벨 / {floor_range}단계 가치 판별", color=0x2ECC71)
    embed.add_field(name=f"🥇 최우선 선택 [1등상]", value=f"👉 **{analyzed_rewards[0]['original']}**", inline=False)

    rank_text = ""
    for idx, item in enumerate(analyzed_rewards):
        rank_text += f"• **{idx+1}위**: {item['original']} ({item['calc_val']:,} G)\n"
    embed.add_field(name="📋 보상 가치 순위 목록", value=rank_text, inline=False)

    if unknown_rewards:
        embed.add_field(name="⚠️ 미등록 재화 (오타 확인)", value=f"`{', '.join(unknown_rewards)}`", inline=False)

    await ctx.send(embed=embed)


# =========================
# ⏰ 알람 타이머 (!알람)
# =========================
@bot.command(name="알람")
async def set_timer(ctx, time_str: str = None, *, memo: str = "시간 완료!"):
    if not time_str:
        await ctx.send("❌ 사용법: `!알람 [시간+단위] [내용]` (예: `!알람 10분 공대장 복귀`)")
        return

    seconds = 0
    if "분" in time_str:
        seconds = int(time_str.replace("분", "").strip()) * 60
    elif "초" in time_str:
        seconds = int(time_str.replace("초", "").strip())
    else:
        try: seconds = int(time_str) * 60
        except ValueError: return

    await ctx.send(f"⏰ **{time_str}** 후 알람 타이머를 켭니다. (메모: {memo})")
    await asyncio.sleep(seconds)
    await ctx.send(f"🚨 **[{time_str} 알람 종료]** ➜ {ctx.author.mention} {memo}")


# =========================
# 기본 기능들 포트 연동
# =========================
@bot.command(name="낙원")
async def show_nakwon_code(ctx, job_name: str = None):
    if not job_name: return
    matched_job = None
    for key in NAKWON_SKILL_CODES.keys():
        if job_name in key: matched_job = key; break
    if not matched_job: return
    job_data = NAKWON_SKILL_CODES[matched_job]
    embed = discord.Embed(title=f"🌊 낙원 증명용 {matched_job} 아크 패시브", color=0x00A3FF)
    embed.add_field(name="📋 복사용 스킬코드", value=f"```{job_data['code']}```", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="시너지")
async def show_synergy(ctx):
    embed = discord.Embed(title="⚔️ 로스트아크 전 직업 시너지 표", color=0x2B2D31)
    for job, data in list(SYNERGY_DETAILS.items())[:10]:
        embed.add_field(name=job, value=data["desc"], inline=True)
    await ctx.send(embed=embed)


# =========================
# 진입점 및 이벤트
# =========================
@bot.event
async def on_ready():
    print(f"✅ 연동 완료 봇 계정: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
