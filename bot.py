import discord
from discord.ext import commands
import requests
import os
import re
import urllib.parse
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import random

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOSTARK_API_KEY = os.getenv("LOSTARK_API_KEY")

if LOSTARK_API_KEY:
    LOSTARK_API_KEY = str(LOSTARK_API_KEY).strip().replace('"', '').replace("'", "").replace("bearer ", "").replace("Bearer ", "")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# ⚙️ 개별 API 호출 헬퍼
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
# 🏛️ 데이터베이스 (낙원, 시너지, 지옥/나락 보상, 수익 계산기)
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
    "어빌리티스톤": 35000, "어빌": 35000, "돌": 35000,
    "특수재련": 28000, "특재": 28000,
    "재련보조": 22000, "보조": 22000, "숨결": 22000,
    "젬선택": 20000, "보석": 20000, "젬": 20000,
    "아비도스융화재료": 18000, "아비도스": 18000, "융화재료": 18000,
    "파괴석수호석결정": 15000, "파괴석": 15000, "수호석": 15000, "결정": 15000,
    "팔찌": 14000,
    "운명의돌혼돈의돌": 12000, "운돌": 12000, "혼돌": 12000,
    "귀속골드": 10000, "골드": 10000,
    "천상도전권": 5000, "도전권": 5000,
    "돌파석": 2000
}

NARAK_DATA = {
    "1750": {"어빌": 7409658, "보석": 2046000, "재련보조": 2023500, "각인서": 1955600, "팔찌": 1500000, "돌": 1350000, "젬": 1091081, "골드": 780000, "카드": 21000},
    "1730": {"어빌": 6736053, "보석": 1705000, "재련보조": 1704000, "각인서": 1564480, "팔찌": 1200000, "돌": 1080000, "젬": 935212, "골드": 650000},
    "1700": {"어빌": 5052039, "보석": 1364000, "재련보조": 1363200, "각인서": 1173360, "돌": 900000, "팔찌": 800000, "골드": 540000, "젬": 304535},
    "1640": {"어빌": 4041632, "보석": 1023000, "재련보조": 1011750, "골드": 480000, "팔찌": 375000, "돌": 360000}
}

GOLD_TABLE = [
    (1750, 9999, "4막하드+종막하드+세르카나메", 140000, 0),
    (1740, 1749, "4막하드+종막하드+세르카나메", 140000, 0),
    (1730, 1739, "4막하드+종막하드+세르카하드", 130000, 0),
    (1720, 1729, "4막하드+종막노말+세르카노말", 70000, 32000),
    (1710, 1719, "4막노말+종막노말+세르카노말", 45500, 45500),
    (1700, 1709, "4막노말+3막하드+2막하드", 38500, 38500),
    (1690, 1699, "3막노말+2막하드+1막하드", 31000, 31000),
    (1680, 1689, "3막노말+2막노말+1막하드", 27750, 27750),
    (1670, 1679, "2막노말+1막노말+서막하드", 17600, 17600),
    (1660, 1669, "1막노말+서막하드+베히모스", 12950, 12950),
    (1640, 1659, "서막하드+베히모스+카멘하드", 7200, 20200),
    (0, 1639, "골드 획득 불가 배럭", 0, 0)
]


# =========================
# 🛡️ 상세 캐릭터 정보실 UI (!정보)
# =========================
@bot.command(name="정보")
async def character_spec_search(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!정보 [캐릭터이름]`", delete_after=10)
        return
        
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 데이터를 추적 중입니다...")
    
    try:
        profile = call_lostark_api("profiles", character_name)
        if not profile:
            await status_msg.edit(content=f"❌ **{character_name}** 님의 정보를 찾을 수 없습니다.", delete_after=10)
            return
            
        engravings_data = call_lostark_api("engravings", character_name) or {}
        equipment = call_lostark_api("equipment", character_name) or []
        arkpassive_data = call_lostark_api("arkpassive", character_name) or {}

        char_name = profile.get("CharacterName", character_name)
        char_class = profile.get("CharacterClassName", "알 수 없음")
        server_name = profile.get("ServerName", "알 수 없음")
        title = profile.get("Title") or "칭호 없음"
        guild_name = profile.get("GuildName") or "없음"
        item_lvl = str(profile.get("ItemAvgLevel", "0")).replace(",", "")
        exp_exp = str(profile.get("ExpeditionLevel", "0"))
        exp_lvl = str(profile.get("CharacterLevel", "0"))
        
        attack_power = "0"
        combat_stats = {}
        for stat in profile.get("Stats") or []:
            s_type = str(stat.get("Type", ""))
            s_value = str(stat.get("Value", "0"))
            clean_val = re.sub(r'[^\d]', '', s_value)
            if not clean_val.isdigit(): continue
            int_val = int(clean_val)
            if s_type == "공격력": attack_power = f"{int_val:,}"
            elif s_type in ["치명", "특화", "신속", "제압", "인내", "숙련"]: combat_stats[s_type] = int_val
                
        top_stats = sorted(combat_stats.items(), key=lambda x: x[1], reverse=True)[:2]
        stat_text = " / ".join([f"{k} {v}" for k, v in top_stats]) if top_stats else "특성 정보 없음"

        points_info = []
        is_ark_passive = False
        if arkpassive_data:
            is_ark_passive = arkpassive_data.get("IsEffect", False)
            for p in (arkpassive_data.get("Points") or []):
                p_name = p.get("Name", "")
                p_val = p.get("Value", 0)
                if p_name: points_info.append(f"{p_name} {p_val}P")
                    
        ark_passive_status = " | ".join(points_info) if points_info else "포인트 분배 정보 없음"
        if not is_ark_passive: ark_passive_status = "비활성화 상태"

        weapon_name = "장비 정보 없음"
        armor_set_name = "장비 정보 없음"
        for item in equipment:
            i_type = item.get("Type", "")
            clean_name = re.sub(r'<[^>]*>|\[.*?\]|\+\d+\s+', '', item.get("Name", "")).strip()
            if i_type == "무기": weapon_name = clean_name
            elif i_type in ["투구", "상의", "하의", "장갑", "어깨"] and armor_set_name == "장비 정보 없음":
                armor_set_name = re.sub(r'투구|상의|하의|장갑|어깨', '', clean_name).strip()

        eng_text = ""
        seen_engs = set()
        def add_eng(e_name):
            nonlocal eng_text
            if e_name and "감소" not in e_name:
                e_name = e_name.strip()
                if e_name not in seen_engs:
                    seen_engs.add(e_name)
                    eng_text += f"• {e_name}\n"

        if engravings_data:
            for eng in engravings_data.get("Effects") or []:
                add_eng(eng.get("Name", ""))
            for eng in engravings_data.get("ArkPassiveEffects") or []:
                add_eng(eng.get("Name", ""))
                
        if not eng_text: eng_text = "• 활성화된 각인 정보 없음"

        embed = discord.Embed(
            title=f"🎭 {server_name} | {char_name}", 
            description=f"**{char_class}** 세팅 정보 실시간 동기화\n칭호: `{title}` ㅤ|ㅤ 길드: `{guild_name}`",
            color=0x2B2D31
        )
        if profile.get("CharacterImage"): embed.set_thumbnail(url=profile["CharacterImage"])

        embed.add_field(name="📋 기본 정보", value=f"• 아이템 Lv: `{item_lvl}`\n• 원정대 Lv: `{exp_exp}`\n• 전투 Lv: `Lv.{exp_lvl}`", inline=True)
        embed.add_field(name="🔥 핵심 스탯", value=f"• 공격력: `{attack_power}`\n• 특성비: `{stat_text}`", inline=True)
        embed.add_field(name="✨ 장비 세팅", value=f"• 무기: `{weapon_name}`\n• 방어구 세트: `{armor_set_name}`", inline=True)
        embed.add_field(name="⚡ 아크 패시브 가동 스펙", value=f"```md\n[현재 분배 스펙]\n➜ {ark_passive_status}```", inline=False)
        embed.add_field(name="🔸 장착 각인 시스템", value=eng_text, inline=False)

        await status_msg.delete()
        await ctx.send(embed=embed, delete_after=900)
    except Exception as e:
        await status_msg.edit(content=f"❌ 데이터 처리 중 오류가 발생했습니다.\n디버그 코드: `{e}`", delete_after=10)


# =========================
# 🌋 나락 보상 판별기 (!나락추천)
# =========================
@bot.command(name="나락추천")
async def recommend_narak_reward(ctx, level: str, floor: int, *rewards: str):
    if level not in NARAK_DATA:
        await ctx.send("❌ 지원하지 않는 레벨입니다. (1640, 1700, 1730, 1750 중 선택)", delete_after=10)
        return
    if len(rewards) < 1:
        await ctx.send("❌ **사용법:** `!나락추천 [레벨] [층수] [보상1] [보상2] ...`", delete_after=10)
        return
    
    filtered_rewards, skipped = [], []
    for r in rewards:
        clean_r = r.replace(" ", "")
        if "보석" in clean_r and floor < 80:
            skipped.append(clean_r)
            continue
        found_val = 0
        for key, val in NARAK_DATA[level].items():
            if key in clean_r:
                found_val = val
                break
        if found_val > 0: filtered_rewards.append({"name": clean_r, "val": found_val})
        else: skipped.append(clean_r)

    if not filtered_rewards:
        embed = discord.Embed(title="❌ 유효한 보상이 없습니다.", color=0xE74C3C)
        if skipped: embed.description = f"입력하신 보상(`{', '.join(skipped)}`)은 조건에 맞지 않거나 오타입니다."
        await ctx.send(embed=embed, delete_after=10)
        return

    filtered_rewards.sort(key=lambda x: x["val"], reverse=True)
    embed = discord.Embed(title=f"🏆 [나락 보상] {level}Lv / {floor}층 효율 추천", color=0x9B59B6)
    embed.add_field(name="🥇 1등 보상 (가장 추천)", value=f"👉 **{filtered_rewards[0]['name']}**", inline=False)
    
    rank_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅"]
    for i, item in enumerate(filtered_rewards):
        medal = medals[i] if i < len(medals) else "•"
        rank_text += f"{medal} {i+1}위: {item['name']}\n"
    embed.add_field(name="📋 보상 선택 우선순위", value=rank_text, inline=False)
    await ctx.send(embed=embed, delete_after=900)


# =========================
# 🌋 기존 지옥 보상 판별기 (!지옥추천)
# =========================
@bot.command(name="지옥추천")
async def recommend_hell_reward(ctx, level: str, floor_range: str, *rewards: str):
    if not level or not floor_range or len(rewards) < 2:
        await ctx.send("❌ **사용법:** `!지옥추천 [레벨] [층수구간] [보상1] [보상2] ...`", delete_after=10)
        return

    level_multiplier = 4.0 if level == "1750" else (2.5 if level == "1730" else (1.0 if level == "1700" else 0.5))
    try:
        clean_floor = floor_range.replace("층", "")
        if "~" in clean_floor:
            parts = clean_floor.split("~")
            target_floor = (int(parts[0]) + int(parts[1])) / 2
        elif "-" in clean_floor:
            parts = clean_floor.split("-")
            target_floor = (int(parts[0]) + int(parts[1])) / 2
        else:
            target_floor = int(clean_floor)
    except ValueError:
        target_floor = 5
    
    floor_multiplier = 1.0 + (target_floor / 20.0)
    analyzed_rewards, unknown_rewards = [], []

    for r_input in rewards:
        clean_input = r_input.replace(" ", "")
        if clean_input in BASE_REWARD_VALUES:
            base_val = BASE_REWARD_VALUES[clean_input]
            if clean_input in ["아비도스", "융화재료", "파괴석", "수호석", "결정", "돌파석"]:
                final_value = base_val * level_multiplier * floor_multiplier
            else:
                final_value = base_val * level_multiplier * (1.0 + (target_floor / 50.0))
            analyzed_rewards.append({"original": r_input, "calc_val": final_value})
        else:
            unknown_rewards.append(r_input)

    if not analyzed_rewards:
        await ctx.send("❌ 인식된 보상이 없습니다.", delete_after=10)
        return

    analyzed_rewards.sort(key=lambda x: x["calc_val"], reverse=True)
    embed = discord.Embed(title=f"🌋 [지옥 보상] {level}레벨 / {floor_range} 구간", color=0x2ECC71)
    embed.add_field(name=f"🥇 지금 이 구간 최고의 [1등상]", value=f"👉 **{analyzed_rewards[0]['original']}**", inline=False)
    
    rank_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅"]
    for idx, item in enumerate(analyzed_rewards):
        medal = medals[idx] if idx < len(medals) else "•"
        rank_text += f"{medal} **{idx+1}위**: {item['original']}\n"
    embed.add_field(name="📋 보상 선택 우선순위", value=rank_text, inline=False)
    await ctx.send(embed=embed, delete_after=900)


# =========================
# ⚖️ 경매 분배금 계산기 (!경매)
# =========================
@bot.command(name="경매")
async def calculate_auction(ctx, price: int = None):
    if not price or price <= 0:
        await ctx.send("❌ 사용법: `!경매 [경매장 시세]`", delete_after=10)
        return

    net_value = int(price * 0.95)
    calc_data = {
        "4인 파티 (군단장)": {"break_even": int(net_value * 3 / 4), "recommend": int(net_value * 0.95 * 3 / 4)},
        "8인 파티 (어비스 레이드)": {"break_even": int(net_value * 7 / 8), "recommend": int(net_value * 0.95 * 7 / 8)},
        "16인 파티 (어비스 던전)": {"break_even": int(net_value * 15 / 16), "recommend": int(net_value * 0.95 * 15 / 16)}
    }

    embed = discord.Embed(title=f"⚖️ 경매 입찰금 정산기 (시세: {price:,} G)", color=0xF1C40F)
    for team, data in calc_data.items():
        embed.add_field(name=f"👥 {team}", value=f"• **추천 입찰가:** `{data['recommend']:,} G`\n• **손익 분기점:** `{data['break_even']:,} G`", inline=False)
    await ctx.send(embed=embed, delete_after=900)


# =========================
# 🌊 지옥 보상효율표 (!지옥효율)
# =========================
@bot.command(name="지옥효율")
async def show_hell_reward_efficiency(ctx):
    embed = discord.Embed(title="🌋 낙원 : 지옥 콘텐츠 구간별 보상 효율표", color=0xE74C3C)
    embed.add_field(name="💎 1700 / 1730 구간", value="• 원정대 스펙업 필수 파밍 구간", inline=False)
    embed.add_field(name="🎲 5회 강하 후 '5층 마무리' 확률", value="• `(1/20)^5` = **0.00003125%**", inline=False)
    await ctx.send(embed=embed, delete_after=900)


# =========================
# ⏰ 알람 타이머 (!알람)
# =========================
@bot.command(name="알람")
async def set_timer(ctx, time_str: str = None, *, memo: str = "시간 완료!"):
    if not time_str:
        await ctx.send("❌ 사용법: `!알람 [시간+단위] [메모]`", delete_after=10)
        return
    seconds = int(time_str.replace("분", "").strip()) * 60 if "분" in time_str else int(time_str)
    await ctx.send(f"⏰ {ctx.author.mention}님, **{time_str}** 알람 시작! ({memo})", delete_after=900)
    await asyncio.sleep(seconds)
    await ctx.send(f"🚨 **[알람 완료]** ➜ {memo}", delete_after=900)


# =========================
# 기본 기능들 (!낙원, !시너지, !레이드조합)
# =========================
@bot.command(name="낙원")
async def show_nakwon_code(ctx, job_name: str = None):
    if not job_name:
        return await ctx.send("❌ 사용법: `!낙원 [직업명]`", delete_after=10)
    matched_job = next((key for key in NAKWON_SKILL_CODES.keys() if job_name in key), None)
    if not matched_job: return await ctx.send("❌ 직업을 찾을 수 없습니다.", delete_after=10)
    job_data = NAKWON_SKILL_CODES[matched_job]
    embed = discord.Embed(title=f"🌊 낙원 증명용 {matched_job} 아크 패시브", color=0x00A3FF)
    embed.add_field(name="📋 스킬코드", value=f"```{job_data['code']}```", inline=False)
    embed.add_field(name="💡 팁", value=job_data['tip'], inline=False)
    await ctx.send(embed=embed, delete_after=900)

@bot.command(name="시너지")
async def show_synergy(ctx):
    embed = discord.Embed(title="⚔️ 로스트아크 전 직업 시너지 표", color=0x2B2D31)
    jobs = list(SYNERGY_DETAILS.keys())
    for i, chunk in enumerate([jobs[i:i + 6] for i in range(0, len(jobs), 6)]):
        embed.add_field(name=f"목록 ({i+1})", value="".join([f"• **{j}**: {SYNERGY_DETAILS[j]['desc']}\n" for j in chunk]), inline=False)
    await ctx.send(embed=embed, delete_after=900)

@bot.command(name="레이드조합")
async def analyze_raid_party(ctx, *jobs: str):
    if len(jobs) < 1 or len(jobs) > 4: return await ctx.send("❌ 사용법: `!레이드조합 [직업1] [직업2] ...`", delete_after=10)
    matched_jobs = []
    for job in jobs:
        for key in SYNERGY_DETAILS.keys():
            if job in key: matched_jobs.append(key); break
    embed = discord.Embed(title="🛡️ 레이드 파티 조합 분석", color=0x3498DB)
    embed.add_field(name="👥 파티원", value=" / ".join(matched_jobs), inline=False)
    await ctx.send(embed=embed, delete_after=900)


# =========================
# ⚔️ 실시간 레이드 모집 UI (!레이드모집)
# =========================
class RaidJoinView(discord.ui.View):
    def __init__(self, title, creator, max_dps, max_supp):
        super().__init__(timeout=None)
        self.title = title
        self.dps_list = [(creator, "공격대장 👑")]
        self.supp_list = []
        self.max_dps = max_dps
        self.max_supp = max_supp
        
    def generate_embed(self):
        embed = discord.Embed(title=f"⚔️ {self.title}", color=0x2B2D31)
        dps_text = [f"• {u.mention} ➜ `{r}`" if u else "• == 빈 자리 ==" for u, r in (self.dps_list + [(None, None)] * self.max_dps)[:self.max_dps]]
        supp_text = [f"• {u.mention} ➜ `{r}`" if u else "• == 빈 자리 ==" for u, r in (self.supp_list + [(None, None)] * self.max_supp)[:self.max_supp]]
        embed.add_field(name=f"딜러 ({len(self.dps_list)}/{self.max_dps})", value="\n".join(dps_text), inline=False)
        embed.add_field(name=f"서포터 ({len(self.supp_list)}/{self.max_supp})", value="\n".join(supp_text), inline=False)
        return embed

    @discord.ui.button(label="딜러 참가", style=discord.ButtonStyle.primary, custom_id="join_dps")
    async def join_dps(self, interaction: discord.Interaction, button: discord.ui.Button):
        if any(u.id == interaction.user.id for u, _ in self.dps_list + self.supp_list): return await interaction.response.send_message("❌ 이미 참가 중입니다.", ephemeral=True)
        if len(self.dps_list) >= self.max_dps: return await interaction.response.send_message("❌ 딜러 만석", ephemeral=True)
        self.dps_list.append((interaction.user, "참가자"))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="서폿 참가", style=discord.ButtonStyle.success, custom_id="join_supp")
    async def join_supp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if any(u.id == interaction.user.id for u, _ in self.dps_list + self.supp_list): return await interaction.response.send_message("❌ 이미 참가 중입니다.", ephemeral=True)
        if len(self.supp_list) >= self.max_supp: return await interaction.response.send_message("❌ 서폿 만석", ephemeral=True)
        self.supp_list.append((interaction.user, "참가자"))
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="참가 취소", style=discord.ButtonStyle.danger, custom_id="leave_raid")
    async def leave_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.dps_list = [item for item in self.dps_list if item[0].id != interaction.user.id]
        self.supp_list = [item for item in self.supp_list if item[0].id != interaction.user.id]
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.command(name="레이드모집")
async def create_raid_party(ctx, size: int = None, *, title: str = "공격대 모집"):
    if size not in [4, 8]: return await ctx.send("❌ 사용법: `!레이드모집 [4/8] [제목]`", delete_after=10)
    view = RaidJoinView(title, ctx.author, 3, 1) if size == 4 else RaidJoinView(title, ctx.author, 6, 2)
    await ctx.send(embed=view.generate_embed(), view=view, delete_after=900)
    

# =========================
# 🎲 큐브 매칭 정산 시스템 (!큐브계산기)
# =========================
class CubeCalculatorModal(discord.ui.Modal, title="🎲 캐릭터별 큐브 매칭 정산"):
    my_tickets = discord.ui.TextInput(label="내 캐릭별 티켓 현황", style=discord.TextStyle.long, required=True)
    partner_tickets = discord.ui.TextInput(label="상대방 캐릭별 티켓 현황", style=discord.TextStyle.long, required=True)

    def parse_tickets_by_char(self, text):
        data = {4: {}, 3: {}, 2: {}, 1: {}}
        for line in text.strip().split('\n'):
            if not line.strip(): continue
            match = re.search(r'([1-4])[^\d]*(\d+)', line)
            if match:
                stage, count = int(match.group(1)), int(match.group(2))
                char_name = line.split(match.group(0))[0].strip() or f"캐릭_{stage}"
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
            embed.add_field(name=f"▶️ {stage}해금 큐브 가이드", value=stage_text, inline=False)
        
        if not has_data: return await interaction.followup.send("❌ 티켓 데이터를 파싱하지 못했습니다.")
        await interaction.followup.send(embed=embed)

class CubeView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="큐브 정산하기", style=discord.ButtonStyle.blurple, custom_id="cube_calc_btn")
    async def cube_calc(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.send_modal(CubeCalculatorModal())


# =========================
# 🛡️ 길드 인증 시스템 (!인증패널)
# =========================
class VerifyModal(discord.ui.Modal, title="로스트아크 인증"):
    character_name = discord.ui.TextInput(label="캐릭터 이름", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        profile = call_lostark_api("profiles", self.character_name.value)
        if not profile: return await interaction.followup.send("❌ 캐릭터 정보를 찾을 수 없습니다.", ephemeral=True)
        member = interaction.guild.get_member(interaction.user.id)
        if member:
            try: await member.edit(nick=f"{profile.get('CharacterName')}/{profile.get('CharacterClassName')}")
            except: pass
        await interaction.followup.send(embed=discord.Embed(title="✅ 인증 완료", color=0x57F287), ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.send_modal(VerifyModal())


# =========================
# 💰 원정대 주간 예상 수익 계산기 (!수익)
# =========================
@bot.command(name="수익")
async def calculate_roster_gold(ctx, character_name: str = None):
    if not character_name:
        await ctx.send("❌ 사용법: `!수익 [캐릭터이름]`", delete_after=10)
        return
        
    status_msg = await ctx.send(f"🔍 **{character_name}** 님의 원정대 최적화 코스를 설계 중입니다...")
    
    try:
        if not LOSTARK_API_KEY:
            return await status_msg.edit(content="❌ API 키가 설정되지 않았습니다.", delete_after=10)
            
        headers = {"accept": "application/json", "authorization": f"bearer {LOSTARK_API_KEY}"}
        encoded_name = urllib.parse.quote(character_name)
        url = f"https://developer-lostark.game.onstove.com/characters/{encoded_name}/siblings"
        
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return await status_msg.edit(content="❌ 원정대 정보를 불러오지 못했습니다. (닉네임 오타 확인)", delete_after=10)
            
        siblings = r.json()
        if not siblings:
            return await status_msg.edit(content="❌ 캐릭터 정보가 없습니다.", delete_after=10)
            
        for char in siblings:
            clean_lvl = str(char.get("ItemAvgLevel", "0")).replace(",", "")
            char["num_lvl"] = float(clean_lvl)
            
        sorted_chars = sorted(siblings, key=lambda x: x["num_lvl"], reverse=True)
        gold_earners = sorted_chars[:6]
        
        roster_unbound = 0
        roster_bound = 0
        
        embed = discord.Embed(title=f"💰 {character_name} 님의 주간 레이드 수익표", color=0x2ECC71)
        embed.description = "💡 템렙 상위 6캐릭 기준, **유통 골드 확보에 가장 유리한 최적 코스**입니다."
        
        for idx, char in enumerate(gold_earners, 1):
            c_name = char.get("CharacterName", "알 수 없음")
            c_class = char.get("CharacterClassName", "")
            c_lvl = char["num_lvl"]
            
            r_desc = "수익 없음"
            u_gold = 0
            b_gold = 0
            
            for min_l, max_l, desc, ug, bg in GOLD_TABLE:
                if min_l <= c_lvl <= max_l:
                    r_desc = desc
                    u_gold = ug
                    b_gold = bg
                    break
                    
            if u_gold == 0 and b_gold == 0:
                embed.add_field(
                    name=f"[{idx}] {c_name} ({c_class}) - Lv.{c_lvl:,.2f}",
                    value="└ 🚫 골드 획득 불가 배럭",
                    inline=False
                )
                continue
                
            total_char_gold = u_gold + b_gold
            roster_unbound += u_gold
            roster_bound += b_gold
            
            val_text = f"🎯 **추천 코스:** `{r_desc}`\n"
            val_text += f"└ 🪙 **유통 가능:** `{u_gold:,} G`\n"
            val_text += f"└ 🔒 **귀속 골드:** `{b_gold:,} G`\n"
            val_text += f"└ 📊 **총합:** `{total_char_gold:,} G`"
            
            embed.add_field(
                name=f"[{idx}] {c_name} ({c_class}) - Lv.{c_lvl:,.2f}",
                value=val_text,
                inline=False
            )
            
        roster_total_val = roster_unbound + roster_bound
        embed.add_field(name="━━━━━━━━━━━━━━━━━━", value="**[ 💸 원정대 주간 예상 총합 ]**", inline=False)
        embed.add_field(name="🪙 기본 분배 (쌀먹/자율)", value=f"• 유통 골드: **{roster_unbound:,} G**\n• 귀속 골드: **{roster_bound:,} G**", inline=True)
        embed.add_field(name="🔒 전액 귀속 (원정대 풀성장)", value=f"• 유통 골드: **0 G**\n• 귀속 골드: **{roster_total_val:,} G**", inline=True)
        
        await status_msg.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        await status_msg.edit(content=f"❌ 데이터 처리 중 오류가 발생했습니다.\n디버그 코드: `{e}`", delete_after=10)


# =========================
# 🧹 채팅 정리 명령어 (!정리)
# =========================
@bot.command(name="정리")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, count: int = 10):
    deleted = await ctx.channel.purge(limit=count + 1)
    await ctx.send(f"✅ **{len(deleted)-1}개**의 메시지를 정리했습니다.", delete_after=5)


# =========================
# 🎲 디스코드판 '티카투카' 보드게임 (!티카투카)
# =========================
class TikaTukaGameView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=None)
        self.p1 = p1
        self.p2 = p2
        self.current_player = p1
        
        self.board = {
            p1.id: [[], [], []], 
            p2.id: [[], [], []]
        }
        
        self.current_dice = random.randint(1, 6)
        self.is_shield_dice = True  
        self.has_reroll = {p1.id: True, p2.id: True}
        self.message = "게임 시작! 첫 턴은 🛡️실드 주사위가 지급됩니다. (반드시 내 보드에 배치)"

    def calc_score(self, col):
        if not col: return 0
        score = 0
        vals = [d["val"] for d in col]
        for num in set(vals):
            count = vals.count(num)
            score += (num * count) * count
        return score

    def is_board_full(self, user_id):
        return all(len(self.board[user_id][i]) >= 3 for i in range(3))

    def generate_embed(self):
        embed = discord.Embed(
            title=f"🎲 티카투카 대결! ({self.p1.display_name} vs {self.p2.display_name})",
            color=0xF1C40F
        )
        dice_type_str = "🛡️ [실드 주사위]" if self.is_shield_dice else "🎲 [일반 주사위]"
        desc = f"🔔 현재 턴: **{self.current_player.mention} 님의 차례입니다!**\n"
        desc += f"나온 주사위: {dice_type_str} **[ {self.current_dice} ]**\n"
        if self.message:
            desc += f"\n> {self.message}\n"
        embed.description = desc
        
        for player in [self.p1, self.p2]:
            total_score = 0
            board_text = ""
            for i in range(3):
                col = self.board[player.id][i]
                c_score = self.calc_score(col)
                total_score += c_score
                display_col = []
                for d in col:
                    tag = "🛡️" if d["is_shield"] else ""
                    display_col.append(f"[{d['val']}{tag}]")
                display_col += ["□"] * (3 - len(col))
                board_text += f"{i+1}번 줄 ({c_score}점): {' '.join(display_col)}\n"
                
            side = "왼쪽 (나)" if player == self.p1 else "오른쪽 (상대)"
            if player == self.current_player:
                side += " ◀ (현재 턴)"
            embed.add_field(
                name=f"👤 {player.display_name} [{side}] - 총점: {total_score}점",
                value=f"```\n{board_text}```",
                inline=False
            )
        return embed

    async def check_game_end(self, interaction):
        p1_full = self.is_board_full(self.p1.id)
        p2_full = self.is_board_full(self.p2.id)
        if p1_full and p2_full:
            p1_wins = 0
            p2_wins = 0
            p1_total = sum([self.calc_score(c) for c in self.board[self.p1.id]])
            p2_total = sum([self.calc_score(c) for c in self.board[self.p2.id]])
            for i in range(3):
                s1 = self.calc_score(self.board[self.p1.id][i])
                s2 = self.calc_score(self.board[self.p2.id][i])
                if s1 > s2: p1_wins += 1
                elif s2 > s1: p2_wins += 1
            winner_text = ""
            if p1_wins >= 2: winner_text = f"🎉 승자: **{self.p1.display_name}** (줄 승리 우세: {p1_wins} vs {p2_wins})"
            elif p2_wins >= 2: winner_text = f"🎉 승자: **{self.p2.display_name}** (줄 승리 우세: {p2_wins} vs {p1_wins})"
            else:
                if p1_total > p2_total: winner_text = f"🎉 승자: **{self.p1.display_name}** (줄 동률, 총점 우세: {p1_total} vs {p2_total})"
                elif p2_total > p1_total: winner_text = f"🎉 승자: **{self.p2.display_name}** (줄 동률, 총점 우세: {p2_total} vs {p1_total})"
                else: winner_text = "🤝 완벽한 무승부입니다!"
            end_embed = discord.Embed(title="🏁 티카투카 게임 종료!", description=winner_text, color=0x2ECC71)
            for ch in self.children: ch.disabled = True
            await interaction.response.edit_message(embed=end_embed, view=self)
            return True
        return False

    @discord.ui.button(label="내 보드 1번", style=discord.ButtonStyle.primary, row=0)
    async def my_col_1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, True, 0)
    @discord.ui.button(label="내 보드 2번", style=discord.ButtonStyle.primary, row=0)
    async def my_col_2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, True, 1)
    @discord.ui.button(label="내 보드 3번", style=discord.ButtonStyle.primary, row=0)
    async def my_col_3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, True, 2)

    @discord.ui.button(label="상대 보드 1번", style=discord.ButtonStyle.danger, row=1)
    async def opp_col_1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, False, 0)
    @discord.ui.button(label="상대 보드 2번", style=discord.ButtonStyle.danger, row=1)
    async def opp_col_2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, False, 1)
    @discord.ui.button(label="상대 보드 3번", style=discord.ButtonStyle.danger, row=1)
    async def opp_col_3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_placement(interaction, False, 2)

    @discord.ui.button(label="🔄 리롤권 사용 (1회)", style=discord.ButtonStyle.secondary, row=2, custom_id="btn_reroll")
    async def use_reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.current_player.id:
            return await interaction.response.send_message("❌ 당신의 턴이 아닙니다!", ephemeral=True)
        if not self.has_reroll[self.current_player.id]:
            return await interaction.response.send_message("❌ 이미 리롤권을 모두 사용하셨습니다!", ephemeral=True)
        self.has_reroll[self.current_player.id] = False
        old_dice = self.current_dice
        self.current_dice = random.randint(1, 6)
        self.message = f"🔄 리롤 사용 완료! 기존 [{old_dice}] ➜ 새 주사위 **[{self.current_dice}]**"
        button.label = "🔄 리롤권 소모됨"
        button.disabled = True
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    async def handle_placement(self, interaction: discord.Interaction, is_mine: bool, col_idx: int):
        if interaction.user.id != self.current_player.id:
            return await interaction.response.send_message("❌ 당신의 턴이 아닙니다!", ephemeral=True)
        is_first_turn = all(len(self.board[self.p1.id][i]) == 0 for i in range(3)) and all(len(self.board[self.p2.id][i]) == 0 for i in range(3))
        if is_first_turn and not is_mine:
            return await interaction.response.send_message("❌ 최초 게임 시작 🛡️실드 주사위는 반드시 '내 보드'에 배치해야 합니다!", ephemeral=True)
        if not is_mine and not self.is_shield_dice:
            return await interaction.response.send_message("❌ 🎲일반 주사위는 '내 보드'에만 배치할 수 있습니다!", ephemeral=True)
        target_player = self.current_player if is_mine else (self.p2 if self.current_player == self.p1 else self.p1)
        target_col = self.board[target_player.id][col_idx]
        if len(target_col) >= 3:
            return await interaction.response.send_message("❌ 해당 줄은 이미 꽉 찼습니다! 다른 줄을 선택해 주세요.", ephemeral=True)
        self.message = ""
        alkkagi_triggered = False
        if is_mine and not self.is_shield_dice:
            opponent = self.p2 if self.current_player == self.p1 else self.p1
            opp_col = self.board[opponent.id][col_idx]
            has_destructible = any(d["val"] == self.current_dice and not d["is_shield"] for d in opp_col)
            if has_destructible:
                self.board[opponent.id][col_idx] = [d for d in opp_col if not (d["val"] == self.current_dice and not d["is_shield"])]
                alkkagi_triggered = True
                self.message = f"💥 **알까기 성공!** 내 주사위와 상대방의 일반 주사위가 소멸했습니다! 보상으로 🛡️ **실드 주사위**를 받아 연속으로 배치하세요!"
        if not alkkagi_triggered:
            target_col.append({"val": self.current_dice, "is_shield": self.is_shield_dice})
        if await self.check_game_end(interaction): return
        if alkkagi_triggered:
            self.is_shield_dice = True
            self.current_dice = random.randint(1, 6)
        else:
            next_player = self.p2 if self.current_player == self.p1 else self.p1
            if self.is_board_full(next_player.id):
                self.message += f"\n⚠️ {next_player.display_name}님의 보드가 꽉 차서 턴이 스킵되었습니다!"
                self.is_shield_dice = False
                self.current_dice = random.randint(1, 6)
            else:
                self.current_player = next_player
                self.is_shield_dice = False
                self.current_dice = random.randint(1, 6)
        for child in self.children:
            if getattr(child, "custom_id", "") == "btn_reroll":
                can_reroll = self.has_reroll[self.current_player.id]
                child.label = "🔄 리롤권 사용 (1회)" if can_reroll else "🔄 리롤권 소모됨"
                child.disabled = not can_reroll
                break
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        ping_msg = await interaction.channel.send(f"💥 {self.current_player.mention} 님, 알까기 성공 연속 턴!" if alkkagi_triggered else f"🔔 {self.current_player.mention} 님, 차례입니다!")
        await ping_msg.delete(delay=3)

@bot.command(name="티카투카")
async def start_tikatuka(ctx, opponent: discord.Member):
    if opponent.bot or opponent == ctx.author:
        return await ctx.send("❌ 대결할 다른 길드원을 올바르게 멘션해 주세요!", delete_after=10)
    view = TikaTukaGameView(ctx.author, opponent)
    await ctx.send(embed=view.generate_embed(), view=view)
    ping_msg = await ctx.send(f"🔔 {ctx.author.mention}님, 게임이 시작되었습니다! 첫 차례입니다!")
    await ping_msg.delete(delay=3)


# =========================
# 🂿 도둑잡기 보드게임 시스템
# =========================
thief_games = {}

class ThiefGameView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=None)
        self.game_data = game_data

    @discord.ui.button(label="내 손패 보기 (DM)", style=discord.ButtonStyle.primary, custom_id="check_hand")
    async def check_hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.game_data["players"]:
            return await interaction.response.send_message("❌ 이 게임에 참여하지 않으셨습니다.", ephemeral=True)
        hand = self.game_data["hands"][interaction.user.id]
        hand_str = " ".join([f"`[{c}]`" for c in hand]) if hand else "없음 (탈출 성공!)"
        await interaction.response.send_message(f"🎴 **[현재 내 손패]**\n{hand_str}", ephemeral=True)

class TargetSelectView(discord.ui.View):
    def __init__(self, game_data, target_player):
        super().__init__(timeout=60)
        self.game_data = game_data
        self.target_player = target_player
        target_hand = self.game_data["hands"][target_player.id]
        for i in range(len(target_hand)):
            self.add_item(ThiefCardButton(i, f"{i+1}번째 카드"))

class ThiefCardButton(discord.ui.Button):
    def __init__(self, card_idx, label):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.card_idx = card_idx

    async def callback(self, interaction: discord.Interaction):
        view: TargetSelectView = self.view
        game = view.game_data
        if interaction.user != game["current_player"]:
            return await interaction.response.send_message("❌ 당신의 차례가 아닙니다!", ephemeral=True)
        target = view.target_player
        target_hand = game["hands"][target.id]
        if self.card_idx >= len(target_hand):
            return await interaction.response.send_message("❌ 이미 선택되었거나 존재하지 않는 카드입니다.", ephemeral=True)
        drawn_card = target_hand.pop(self.card_idx)
        current_hand = game["hands"][interaction.user.id]
        current_hand.append(drawn_card)
        removed_pairs = []
        cleaned_hand = []
        card_counts = {}
        for c in current_hand:
            card_counts[c] = card_counts.get(c, 0) + 1
        for c in current_hand:
            if c == "🂿 조커": cleaned_hand.append(c)
            elif card_counts[c] % 2 == 0: removed_pairs.append(c)
            else: cleaned_hand.append(c)
        game["hands"][interaction.user.id] = cleaned_hand
        result_desc = f"✨ **{interaction.user.display_name}** 님이 **{target.display_name}** 님의 패에서 **`{drawn_card}`**을(를) 뽑았습니다!"
        if removed_pairs:
            result_desc += f"\n🗑️ 짝이 맞아 버려진 카드: {', '.join([f'`{p}`' for p in set(removed_pairs)])}"
        for p in [interaction.user, target]:
            if len(game["hands"][p.id]) == 0 and p not in game["eliminated"]:
                game["eliminated"].append(p)
                result_desc += f"\n🎉 **{p.display_name} 님께서 모든 패를 털어내고 탈출하셨습니다!**"
        active_players = [p for p in game["players"] if p not in game["eliminated"]]
        if len(active_players) <= 1:
            loser = active_players[0] if active_players else target
            end_embed = discord.Embed(title="🏁 도둑잡기 게임 종료!", description=f"🚨 끝까지 🂿조커(도둑)를 손에 쥐고 있던 **{loser.mention}** 님이 도둑으로 검거되었습니다!", color=0xE74C3C)
            await interaction.response.edit_message(content=result_desc, embed=end_embed, view=None)
            return
        curr_idx = game["players"].index(game["current_player"])
        while True:
            curr_idx = (curr_idx + 1) % len(game["players"])
            next_p = game["players"][curr_idx]
            if next_p not in game["eliminated"]:
                game["current_player"] = next_p
                break
        await interaction.response.edit_message(content=result_desc, view=None)
        board_view = ThiefGameView(game)
        embed = discord.Embed(title="🃏 도둑잡기 진행 중...", color=0x3498DB)
        status_text = ""
        for p in game["players"]:
            if p in game["eliminated"]: status_text += f"• ~~{p.display_name}~~ ➜ **탈출 완료! 🎉**\n"
            else:
                card_count = len(game["hands"][p.id])
                is_turn = " ◀ (현재 턴)" if p == game["current_player"] else ""
                status_text += f"• {p.mention} ➜ 손패 **{card_count}장**{is_turn}\n"
        embed.description = status_text
        await game["message"].edit(embed=embed, view=board_view)
        active_idx = game["players"].index(game["current_player"])
        target_p = None
        for i in range(1, len(game["players"])):
            cand = game["players"][(active_idx + i) % len(game["players"])]
            if cand not in game["eliminated"]:
                target_p = cand
                break
        if target_p:
            select_view = TargetSelectView(game, target_p)
            await game["channel"].send(f"👉 **{game['current_player'].display_name}** 님 차례입니다! **{target_p.display_name}** 님의 패 중에서 뽑을 카드를 선택하세요:", view=select_view)
            ping_msg = await game["channel"].send(f"🔔 {game['current_player'].mention} 님, 차례입니다!")
            await ping_msg.delete(delay=3)

@bot.command(name="도둑잡기모집")
async def start_thief_lobby(ctx):
    thief_games[ctx.guild.id] = {"status": "recruiting", "players": [], "channel": ctx.channel}
    await ctx.send(embed=discord.Embed(title="🃏 도둑잡기 로비 생성!", description="참가하실 분들은 `!도둑잡기참가` 를 입력해주세요!", color=0x3498DB))

@bot.command(name="도둑잡기참가")
async def join_thief_game(ctx):
    game = thief_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 모집 중인 게임이 없습니다.", delete_after=10)
    if ctx.author in game["players"]: return await ctx.send("❌ 이미 참가하셨습니다.", delete_after=10)
    game["players"].append(ctx.author)
    await ctx.send(f"✅ **{ctx.author.display_name}**님 도둑잡기 참가 완료!")

@bot.command(name="도둑잡기시작")
async def start_thief_game(ctx):
    game = thief_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 시작할 로비가 없습니다.", delete_after=10)
    players = game["players"]
    if len(players) < 2: return await ctx.send("❌ 최소 2명이 필요합니다.", delete_after=10)
    game["status"] = "playing"
    card_pool = []
    base_cards = ["🍎 사과", "🍌 바나나", "🍇 포도", "🍉 수박", "🍓 딸기", "🍑 복숭아", "🍒 체리", "🥝 키위"]
    for c in base_cards: card_pool.extend([c, c])
    card_pool.append("🂿 조커")
    random.shuffle(card_pool)
    hands = {p.id: [] for p in players}
    idx = 0
    while card_pool:
        hands[players[idx % len(players)].id].append(card_pool.pop())
        idx += 1
    for p_id in hands:
        current_hand = hands[p_id]
        cleaned = []
        card_counts = {c: current_hand.count(c) for c in current_hand}
        for c in current_hand:
            if c == "🂿 조커": cleaned.append(c)
            elif card_counts[c] % 2 == 0: pass
            else: cleaned.append(c)
        hands[p_id] = cleaned
    game["hands"] = hands
    game["eliminated"] = []
    game["current_player"] = players[0]
    for p in players:
        try:
            my_hand_str = " ".join([f"`[{c}]`" for c in hands[p.id]])
            await p.send(embed=discord.Embed(title="🃏 도둑잡기 초기 손패", description=my_hand_str, color=0x2ECC71))
        except: pass
    board_view = ThiefGameView(game)
    embed = discord.Embed(title="🃏 도둑잡기 게임 시작!", description="아래 버튼으로 내 손패를 확인하세요!", color=0x3498DB)
    status_text = "".join([f"• {p.mention} ➜ 손패 **{len(hands[p.id])}장**{' ◀ (현재 턴)' if p == game['current_player'] else ''}\n" for p in players])
    embed.add_field(name="👥 플레이어 현황", value=status_text, inline=False)
    msg = await ctx.send(embed=embed, view=board_view)
    game["message"] = msg
    target_p = players[1]
    select_view = TargetSelectView(game, target_p)
    await ctx.send(f"👉 첫 턴인 **{game['current_player'].display_name}** 님! **{target_p.display_name}** 님의 패 중에서 뽑을 카드를 선택하세요:", view=select_view)
    ping_msg = await ctx.send(f"🔔 {game['current_player'].mention}님, 첫 차례입니다!")
    await ping_msg.delete(delay=3)


# =========================
# 🙈 양세찬 게임 시스템
# =========================
yangsechan_games = {}
YANGSECHAN_WORDS = [# 📺 방송인 / 코미디언 / 유튜버 (25명)
    "유재석", "강호동", "신동엽", "백종원", "침착맨", "주호민", "빠니보틀", "곽튜브", "슈카", "풍월량",
    "기안84", "덱스", "이효리", "박명수", "조세호", "지석진", "하하", "노홍철", "이경규", "김종국",
    "유병재", "풍자", "이수근", "탁재훈", "궤도",
    
    # 🎤 아이돌 / 배우 / 스포츠 스타 (25명)
    "아이유", "카리나", "장원영", "제니", "지수", "안유진", "윈터", "태연", "차은우", "손흥민",
    "페이커", "김연아", "송강", "박보검", "이도현", "마동석", "손석구", "조정석", "이병헌", "송강호",
    "황정민", "류현진", "오타니", "데프트", "쇼메이커",
    
    # 🎬 애니메이션 / 만화 / 영화 캐릭터 (25개)
    "아이언맨", "스파이더맨", "배트맨", "타노스", "토르", "캡틴 아메리카", "헐크", "데드풀", "슈퍼맨", "원더우먼",
    "피카츄", "도라에몽", "짱구", "원피스 루피", "나루토", "손오공", "베지터", "엘사", "올라프", "스폰지밥",
    "징징이", "뚱이", "뽀로로", "펭수", "라이언",
    
    # 🧸 핫한 굿즈 / 밈 / 추억의 캐릭터 (15개)
    "춘식이", "어피치", "치이카와", "하치와루", "우사기", "토토로", "둘리", "영심이", "슬램덩크 강백호", "서태웅",
    "정대만", "미니언", "슈렉", "핑크퐁", "샌즈",
    
    # 📜 역사 위인 (10명)
    "이순신", "세종대왕", "단군", "안중근", "을지문덕", "신사임당", "광해군", "허준", "장영실", "정약용"]

class YangSeChanView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=None)
        self.game_data = game_data
        for player in game_data["players"]:
            if player not in game_data["winners"]:
                self.add_item(YangSeChanButton(player))
        self.add_item(GuessSuccessButton())

class YangSeChanButton(discord.ui.Button):
    def __init__(self, target_player):
        super().__init__(label=f"{target_player.display_name}의 제시어", style=discord.ButtonStyle.secondary)
        self.target_player = target_player

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game_data
        if interaction.user not in game["players"]:
            return await interaction.response.send_message("❌ 게임 참가자가 아닙니다.", ephemeral=True)
        if interaction.user.id == self.target_player.id:
            return await interaction.response.send_message("❌ 자신의 제시어는 절대 볼 수 없습니다!", ephemeral=True)
        word = game["words"][self.target_player.id]
        await interaction.response.send_message(f"👀 **{self.target_player.display_name}** 님의 이마에 붙은 제시어는 **[{word}]** 입니다!", ephemeral=True)

class GuessSuccessButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎉 내 정답 맞춤!", style=discord.ButtonStyle.success, row=4)

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game_data
        if interaction.user not in game["players"]: return await interaction.response.send_message("❌ 참가자가 아닙니다.", ephemeral=True)
        if interaction.user in game["winners"]: return await interaction.response.send_message("❌ 이미 통과하셨습니다!", ephemeral=True)
        word = game["words"][interaction.user.id]
        game["winners"].append(interaction.user)
        result_desc = f"🎊 **{interaction.user.mention}** 님이 정답 **[{word}]** 을(를) 맞추고 통과하셨습니다!"
        remaining = [p for p in game["players"] if p not in game["winners"]]
        if len(remaining) <= 1:
            loser = remaining[0] if remaining else None
            end_desc = result_desc + "\n\n🏁 **게임 종료!**" + (f"\n💀 꼴찌: **{loser.mention}**" if loser else "")
            await interaction.response.edit_message(embed=discord.Embed(title="🙈 양세찬 게임 종료!", description=end_desc, color=0x2ECC71), view=None)
        else:
            await interaction.response.edit_message(content=result_desc, view=YangSeChanView(game))

@bot.command(name="양세찬모집")
async def ysc_lobby(ctx):
    yangsechan_games[ctx.guild.id] = {"status": "recruiting", "players": [], "channel": ctx.channel}
    await ctx.send(embed=discord.Embed(title="🙈 양세찬 게임 모집!", description="`!양세찬참가` 를 입력해주세요!", color=0xF1C40F))

@bot.command(name="양세찬참가")
async def ysc_join(ctx):
    game = yangsechan_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 모집 중인 게임이 없습니다.", delete_after=10)
    if ctx.author in game["players"]: return await ctx.send("❌ 이미 참가하셨습니다.", delete_after=10)
    game["players"].append(ctx.author)
    await ctx.send(f"✅ **{ctx.author.display_name}**님 양세찬 참가 완료!")

@bot.command(name="양세찬시작")
async def ysc_start(ctx):
    game = yangsechan_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 시작할 로비가 없습니다.", delete_after=10)
    players = game["players"]
    if len(players) < 2: return await ctx.send("❌ 최소 2명이 필요합니다.", delete_after=10)
    game["status"] = "playing"
    game["winners"] = []
    game["words"] = {p.id: w for p, w in zip(players, random.sample(YANGSECHAN_WORDS, len(players)))}
    await ctx.send(embed=discord.Embed(title="🙈 양세찬 게임 시작!", description="버튼을 눌러 다른 사람의 제시어를 확인하고 스무고개를 시작하세요!", color=0xF1C40F), view=YangSeChanView(game))


# =========================
# 🕵️ 다빈치 코드 시스템 (정확한 룰 반영)
# =========================
davinci_games = {}

class DavinciGuessModal(discord.ui.Modal, title="🕵️ 타일 추리하기 (색상 + 숫자)"):
    target_idx = discord.ui.TextInput(label="지목할 상대의 타일 번호 (왼쪽부터 1번)", placeholder="예: 2", required=True)
    guessed_input = discord.ui.TextInput(label="색상과 숫자 입력 (예: 흑7, 백-)", placeholder="예: 흑7 또는 백 - (조커는 -)", required=True)

    def __init__(self, game_data, target_player):
        super().__init__()
        self.game_data = game_data
        self.target_player = target_player

    async def on_submit(self, interaction: discord.Interaction):
        game = self.game_data
        if interaction.user != game["current_player"]:
            return await interaction.response.send_message("❌ 당신의 차례가 아닙니다!", ephemeral=True)
            
        try:
            idx = int(self.target_idx.value) - 1
            guess_text = self.guessed_input.value.strip()
        except ValueError:
            return await interaction.response.send_message("❌ 올바른 형식으로 입력해주세요.", ephemeral=True)
            
        target_tiles = game["tiles"][self.target_player.id]
        if idx < 0 or idx >= len(target_tiles):
            return await interaction.response.send_message("❌ 존재하지 않는 타일 번호입니다.", ephemeral=True)
            
        target_tile = target_tiles[idx]
        if not target_tile["hidden"]:
            return await interaction.response.send_message("❌ 이미 공개된 타일입니다!", ephemeral=True)

        # 흑/백 색상 파싱
        guess_color = None
        if "흑" in guess_text or "블랙" in guess_text or "black" in guess_text.lower():
            guess_color = "흑"
        elif "백" in guess_text or "화이트" in guess_text or "white" in guess_text.lower():
            guess_color = "백"
            
        # 숫자 / 조커(-) 파싱
        guess_is_joker = False
        guess_val = None
        if "-" in guess_text or "조커" in guess_text or "joker" in guess_text.lower():
            guess_is_joker = True
            guess_val = -1
        else:
            nums = re.findall(r'\d+', guess_text)
            if nums:
                guess_val = int(nums[0])

        if not guess_color or (guess_val is None and not guess_is_joker):
            return await interaction.response.send_message("❌ 색상(흑/백)과 숫자(0~11 또는 조커는 -)를 모두 포함해서 입력해주세요! (예: 흑7, 백-)", ephemeral=True)

        # 정답 판정 (색상과 숫자가 모두 일치해야 함)
        is_correct = (target_tile["color"] == guess_color) and (
            (target_tile["is_joker"] and guess_is_joker) or 
            (not target_tile["is_joker"] and not guess_is_joker and target_tile["val"] == guess_val)
        )
        
        if is_correct:
            # 추리 성공 시 상대 타일 오픈
            target_tile["hidden"] = False
            
            # 탈락 조건 체크 (모든 타일이 오픈된 플레이어)
            for p in game["players"]:
                if all(not t["hidden"] for t in game["tiles"][p.id]) and p not in game["eliminated"]:
                    game["eliminated"].append(p)
                    
            active_players = [p for p in game["players"] if p not in game["eliminated"]]
            if len(active_players) <= 1:
                winner = active_players[0] if active_players else interaction.user
                end_embed = discord.Embed(title="🏁 다빈치 코드 게임 종료!", description=f"🏆 승리자: **{winner.mention}** 님!", color=0x2ECC71)
                return await interaction.response.edit_message(content=f"🎯 **[추리 성공!]** {interaction.user.display_name} 님이 **{self.target_player.display_name}** 님의 타일 **`{target_tile['display']}`**을(를) 정확히 맞추고 승리하셨습니다!", embed=end_embed, view=None)

            result_text = f"🎯 **[추리 성공! 턴 유지]** {interaction.user.display_name} 님이 **{self.target_player.display_name}** 님의 {idx+1}번째 타일 **`{target_tile['display']}`**을(를) 맞췄습니다!\n👉 계속해서 추리를 이어가세요!"
            
            # 맞히면 턴이 유지되므로 current_player 변경 없이 보드 갱신
            await interaction.response.edit_message(content=result_text, view=None)
            await self.send_board_message(game)
        else:
            # 추리 실패 시 타일 변화 없이 깔끔하게 턴 종료
            result_text = f"❌ **[추리 실패! 턴 종료]** {interaction.user.display_name} 님이 틀렸습니다! (입력: `{guess_text}`)"
            
            # 다음 플레이어로 턴 전환
            curr_idx = game["players"].index(game["current_player"])
            while True:
                curr_idx = (curr_idx + 1) % len(game["players"])
                next_p = game["players"][curr_idx]
                if next_p not in game["eliminated"]:
                    game["current_player"] = next_p
                    break
                    
            await interaction.response.edit_message(content=result_text, view=None)
            await self.send_board_message(game)

    async def send_board_message(self, game):
        embed = discord.Embed(title="🕵️ 다빈치 코드 진행 중", color=0xF1C40F)
        desc = ""
        for p in game["players"]:
            board_str = ""
            for t in game["tiles"][p.id]:
                if t["hidden"]:
                    board_str += "`[ ■ ]` "
                else:
                    board_str += f"`[{t['display']}]` "
            turn_mark = " ◀ (현재 턴)" if p == game["current_player"] else ""
            desc += f"• **{p.display_name}**{turn_mark}\n  └ {board_str}\n"
        embed.description = desc
        
        view = DavinciGameView(game)
        msg = await game["channel"].send(embed=embed, view=view)
        game["message"] = msg
        
        ping_msg = await game["channel"].send(f"🔔 {game['current_player'].mention} 님 차례입니다!")
        await ping_msg.delete(delay=3)

class DavinciGameView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=None)
        self.game_data = game_data
        for p in game_data["players"]:
            if p != game_data["current_player"] and p not in game_data["eliminated"]:
                self.add_item(DavinciTargetButton(p))
        self.add_item(DavinciCheckHandButton())

class DavinciTargetButton(discord.ui.Button):
    def __init__(self, target_player):
        super().__init__(label=f"{target_player.display_name} 지목", style=discord.ButtonStyle.primary)
        self.target_player = target_player
    async def callback(self, interaction: discord.Interaction):
        game = self.view.game_data
        if interaction.user != game["current_player"]: return await interaction.response.send_message("❌ 당신의 차례가 아닙니다!", ephemeral=True)
        await interaction.response.send_modal(DavinciGuessModal(game, self.target_player))

class DavinciCheckHandButton(discord.ui.Button):
    def __init__(self): super().__init__(label="내 타일 보기 (DM)", style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        game = self.view.game_data
        if interaction.user not in game["players"]: return await interaction.response.send_message("❌ 참가자가 아닙니다.", ephemeral=True)
        tiles = game["tiles"][interaction.user.id]
        hand_str = " ".join([f"`[{t['display']}]`" for t in tiles])
        await interaction.response.send_message(f"🎴 **[내 타일 목록]**\n{hand_str}", ephemeral=True)

@bot.command(name="다빈치모집")
async def dv_lobby(ctx):
    davinci_games[ctx.guild.id] = {"status": "recruiting", "players": [], "channel": ctx.channel}
    await ctx.send(embed=discord.Embed(title="🕵️ 다빈치 코드 로비 생성!", description="`!다빈치참가` 를 입력해 참여하세요!", color=0xF1C40F))

@bot.command(name="다빈치참가")
async def dv_join(ctx):
    game = davinci_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 모집 중인 게임이 없습니다.", delete_after=10)
    if ctx.author in game["players"]: return await ctx.send("❌ 이미 참가하셨습니다.", delete_after=10)
    game["players"].append(ctx.author)
    await ctx.send(f"✅ **{ctx.author.display_name}**님 참가 완료!")

@bot.command(name="다빈치시작")
async def dv_start(ctx):
    game = davinci_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 시작할 로비가 없습니다.", delete_after=10)
    players = game["players"]
    if len(players) < 2: return await ctx.send("❌ 최소 2명이 필요합니다.", delete_after=10)
    game["status"] = "playing"
    game["eliminated"] = []
    
    pool = []
    for color in ["흑", "백"]:
        for n in range(12): pool.append({"val": n, "color": color, "is_joker": False, "display": f"{color}{n}", "hidden": True})
        pool.append({"val": -1, "color": color, "is_joker": True, "display": f"{color}-", "hidden": True})
    random.shuffle(pool)
    
    p_count = len(players)
    tile_count = 7 if p_count == 2 else (4 if p_count == 3 else 3)
    
    tiles = {}
    for p in players:
        p_tiles = [pool.pop(0) for _ in range(tile_count)]
        p_tiles.sort(key=lambda x: (99 if x["is_joker"] else x["val"], 0 if x["color"]=="흑" else 1))
        tiles[p.id] = p_tiles
        try:
            my_t = " ".join([f"`[{t['display']}]`" for t in p_tiles])
            await p.send(embed=discord.Embed(title="🕵️ 다빈치 코드 초기 타일", description=my_t, color=0xF1C40F))
        except: pass
        
    game["pool"] = pool
    game["tiles"] = tiles
    game["current_player"] = players[0]
    
    embed = discord.Embed(title="🕵️ 다빈치 코드 게임 시작!", color=0xF1C40F)
    embed.description = "".join([f"• **{p.display_name}**\n  └ " + "`[ ■ ] ` * " * len(tiles[p.id]) + "\n" for p in players])
    msg = await ctx.send(embed=embed, view=DavinciGameView(game))
    game["message"] = msg
    
    ping_msg = await ctx.send(f"🔔 {game['current_player'].mention} 님 첫 차례입니다!")
    await ping_msg.delete(delay=3)

# =========================
# 🦊 라이어 게임 시스템 (주제 투표 + 라이어 찬스 + 제시어 공개)
# =========================
liar_games = {}
LIAR_CATEGORIES = {
    "음식": ["사과", "커피", "라면", "햄버거", "치킨", "김밥", "떡볶이", "초밥"],
    "장소": ["영화관", "지하철", "놀이공원", "수영장", "병원", "공항", "편의점", "PC방"],
    "사물": ["스마트폰", "노트북", "피아노", "시계", "이어폰", "냉장고", "카메라", "선풍기"],
    "직업": ["경찰관", "소방관", "의사", "요리사", "유튜버", "선생님", "운동선수", "배우"]
}

class LiarThemeVoteView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=60)
        self.game_data = game_data
        self.votes = {}
        for theme in LIAR_CATEGORIES.keys(): self.add_item(LiarThemeButton(theme))

class LiarThemeButton(discord.ui.Button):
    def __init__(self, theme):
        super().__init__(label=theme, style=discord.ButtonStyle.secondary)
        self.theme = theme
    async def callback(self, interaction: discord.Interaction):
        game = self.view.game_data
        if interaction.user not in game["players"]: return await interaction.response.send_message("❌ 참가자가 아닙니다.", ephemeral=True)
        self.view.votes[interaction.user.id] = self.theme
        await interaction.response.send_message(f"✅ **[{self.theme}]** 주제 투표 완료!", ephemeral=True)
        if len(self.view.votes) >= len(game["players"]):
            theme_counts = {t: list(self.view.votes.values()).count(t) for t in set(self.view.votes.values())}
            selected_theme = max(theme_counts, key=theme_counts.get)
            secret_word = random.choice(LIAR_CATEGORIES[selected_theme])
            liar = random.choice(game["players"])
            game["liar"] = liar
            game["secret_word"] = secret_word
            game["selected_theme"] = selected_theme
            for p in game["players"]:
                try:
                    if p == liar: await p.send(embed=discord.Embed(title="🦊 [라이어 게임] 역할", description=f"주제: **[{selected_theme}]**\n당신은 **[라이어]**입니다!", color=0xE74C3C))
                    else: await p.send(embed=discord.Embed(title="🦊 [라이어 게임] 역할", description=f"주제: **[{selected_theme}]**\n시민 제시어: **[{secret_word}]**", color=0x3498DB))
                except: pass
            embed = discord.Embed(title=f"🦊 라이어 게임 시작! (주제: {selected_theme})", description="설명을 마치고 아래 버튼으로 라이어를 지목하세요!", color=0xE74C3C)
            await interaction.message.edit(embed=embed, view=LiarVoteView(game))

class LiarFinalGuessModal(discord.ui.Modal, title="🕵️ 라이어의 최후의 제시어 추리"):
    word_guess = discord.ui.TextInput(label="비밀 제시어를 입력하세요", placeholder="예: 사과", required=True)
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data
    async def on_submit(self, interaction: discord.Interaction):
        game = self.game_data
        if interaction.user != game["liar"]: return await interaction.response.send_message("❌ 라이어 본인만 입력 가능!", ephemeral=True)
        guess = self.word_guess.value.strip()
        secret = game["secret_word"].strip()
        if guess == secret:
            end_embed = discord.Embed(title="🔥 라이어 대역전 승리!", description=f"라이어 **{game['liar'].display_name}** 님이 제시어 **[{secret}]**을(를) 맞췄습니다!\n\n🏆 **라이어 승리!**", color=0xE74C3C)
        else:
            end_embed = discord.Embed(title="🎉 시민 측 최종 승리!", description=f"라이어 **{game['liar'].display_name}** 님이 제시어 맞추기에 실패했습니다! (입력: `{guess}`)\n\n🔍 **시민들이 부여받은 제시어는 [{secret}] 였습니다!**\n\n🏆 **시민 승리!**", color=0x2ECC71)
        await interaction.response.send_message(embed=end_embed)

class LiarFinalGuessView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=60)
        self.game_data = game_data
    @discord.ui.button(label="🕵️ 라이어 제시어 맞추기 도전", style=discord.ButtonStyle.danger)
    async def guess_word(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.game_data["liar"]: return await interaction.response.send_message("❌ 라이어 본인만 가능!", ephemeral=True)
        await interaction.response.send_modal(LiarFinalGuessModal(self.game_data))

class LiarVoteModal(discord.ui.Modal, title="🗳️ 라이어 지목하기"):
    target_name = discord.ui.TextInput(label="지목할 유저 닉네임", required=True)
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data
    async def on_submit(self, interaction: discord.Interaction):
        game = self.game_data
        if interaction.user not in game["players"]: return await interaction.response.send_message("❌ 참가자가 아닙니다.", ephemeral=True)
        target = discord.utils.get(game["players"], display_name=self.target_name.value.strip()) or discord.utils.get(game["players"], name=self.target_name.value.strip())
        if not target: return await interaction.response.send_message("❌ 유저를 찾을 수 없습니다.", ephemeral=True)
        game["votes"][interaction.user.id] = target.id
        await interaction.response.send_message(f"✅ **{target.display_name}** 투표 완료!", ephemeral=True)
        if len(game["votes"]) >= len(game["players"]):
            vote_counts = {v: list(game["votes"].values()).count(v) for v in set(game["votes"].values())}
            max_voted_id = max(vote_counts, key=vote_counts.get)
            liar = game["liar"]
            if max_voted_id == liar.id:
                try: await liar.send(f"🕵️ **[최후의 찬스]** 지목당했습니다! 주제는 **[{game['selected_theme']}]** 입니다. 정답을 맞혀보세요!")
                except: pass
                embed = discord.Embed(title="🦊 라이어 검거 성공!", description=f"진짜 라이어 **{liar.display_name}** 님 검거!\n\n**{liar.mention}** 님에게 최후의 찬스가 주어집니다. 정답을 맞히면 역전승!", color=0xE74C3C)
                await interaction.channel.send(embed=embed, view=LiarFinalGuessView(game))
            else:
                voted_person = discord.utils.get(game["players"], id=max_voted_id)
                await interaction.channel.send(embed=discord.Embed(title="🦊 라이어 게임 결과", description=f"🚨 라이어 승리! 무고한 **{voted_person.display_name}** 님을 지목했습니다.\n진짜 라이어: **{liar.display_name}**\n(비밀 제시어: **[{game['secret_word']}]**)", color=0xE74C3C))

class LiarVoteView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=None)
        self.game_data = game_data
    @discord.ui.button(label="🗳️ 범인(라이어) 투표하기", style=discord.ButtonStyle.danger)
    async def open_vote_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LiarVoteModal(self.game_data))

@bot.command(name="라이어모집")
async def liar_lobby(ctx):
    liar_games[ctx.guild.id] = {"status": "recruiting", "players": [], "channel": ctx.channel}
    await ctx.send(embed=discord.Embed(title="🦊 라이어 게임 로비 생성!", description="`!라이어참가` 입력!", color=0xE74C3C))

@bot.command(name="라이어참가")
async def liar_join(ctx):
    game = liar_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 모집 중이 아닙니다.", delete_after=10)
    if ctx.author in game["players"]: return await ctx.send("❌ 이미 참가하셨습니다.", delete_after=10)
    game["players"].append(ctx.author)
    await ctx.send(f"✅ **{ctx.author.display_name}**님 참가 완료!")

@bot.command(name="라이어시작")
async def liar_start(ctx):
    game = liar_games.get(ctx.guild.id)
    if not game or game["status"] != "recruiting": return await ctx.send("❌ 로비가 없습니다.", delete_after=10)
    if len(game["players"]) < 3: return await ctx.send("❌ 최소 3명 필요", delete_after=10)
    game["status"] = "playing"
    game["votes"] = {}
    await ctx.send(embed=discord.Embed(title="🦊 라이어 게임 주제 투표", description="원하는 주제에 투표하세요!", color=0xE74C3C), view=LiarThemeVoteView(game))

# =========================
# 🎨 로아 스티커 (전체 맵 복원)
# =========================
STICKER_MAP = {
    "[토끼모코코]": "https://media.discordapp.net/attachments/1526672551219036263/1526672794199527585/01_RM.gif?ex=6a57e056&is=6a568ed6&hm=d4942c0ec080464f9cf618cbf82a48db544c9d0e08cfc76581a9beb5e35124a5&",
    "[춤]": "https://media.discordapp.net/attachments/1526672551219036263/1526672794530615407/02_RM.gif?ex=6a57e056&is=6a568ed6&hm=9ce50cb3e99e58a1ed13f4e4696d0d1d0392b5bece6fa0dba71533c5bd8b0741&",
    "[하트]": "https://media.discordapp.net/attachments/1526672551219036263/1526672794945978529/03_RM.png?ex=6a57e056&is=6a568ed6&hm=6e5bd6e98258fc1fd4d94ca5038632fd770b01a567f2593f01603bc757706230&=&format=webp&quality=lossless",
    "[핥짝1]": "https://media.discordapp.net/attachments/1526672551219036263/1526672795470139392/04_RM.png?ex=6a57e056&is=6a568ed6&hm=bc71adc8e05d1ff995f6f7064b3fdd2d365f7ab6b493a1fb08656e236c3b6719&=&format=webp&quality=lossless",
    "[초롱]": "https://media.discordapp.net/attachments/1526672551219036263/1526672795780648981/05_RM.gif?ex=6a57e056&is=6a568ed6&hm=644ac64b4e4281f06a135cfba5c36e30f1b604d25fac22035ec4c4b0d3b4982e&",
    "[페로몬]": "https://media.discordapp.net/attachments/1526672551219036263/1526672796162199773/06_RM.png?ex=6a57e056&is=6a568ed6&hm=d229b0c1d590c6ef102a2293020dcd16da5d98eda042cbf5c323e36cab890736&=&format=webp&quality=lossless",
    "[핥짝2]": "https://media.discordapp.net/attachments/1526672551219036263/1526672796560920596/07_RM.png?ex=6a57e056&is=6a568ed6&hm=34fbd6700c4e201eadbdf7d678e80bb6bc7d7b875ad7c4843dbec97c8f7605f8&=&format=webp&quality=lossless",
    "[그만]": "https://media.discordapp.net/attachments/1526672551219036263/1526672854744170647/08_RM.png?ex=6a57e064&is=6a568ee4&hm=452bababbf69217af7fa1a522eb7aeb8a9544b0006b1c4b878c99faed98cabe6&=&format=webp&quality=lossless",
    "[하트2]": "https://media.discordapp.net/attachments/1526672551219036263/1526672855318921306/09_RM.png?ex=6a57e064&is=6a568ee4&hm=4625dc45a1966ad61ce9ced3a562f3443a6bbe27d9d09c6199b85bc4e995314a&=&format=webp&quality=lossless",
    "[고인물]": "https://media.discordapp.net/attachments/1526672551219036263/1526672855801135104/10_RM.png?ex=6a57e065&is=6a568ee5&hm=97a16111c90a486ed64a21a63e3db2c7d55a1548702edb8d8d73a8a4e2be20ea&=&format=webp&quality=lossless",
    "[고인물2]": "https://media.discordapp.net/attachments/1526672551219036263/1526672856342073414/11_RM.png?ex=6a57e065&is=6a568ee5&hm=c56ce161fe20f64c2820c48164b60954005c375d6302fefe86cd41ecfb7b310c&=&format=webp&quality=lossless",
    "[쓰담코]": "https://media.discordapp.net/attachments/1526672551219036263/1526672856728207420/12_RM.png?ex=6a57e065&is=6a568ee5&hm=2a8053c9622ed90d8ffb17419c316434e11b1cd581112f1bfea3b191b771f166&=&format=webp&quality=lossless",
    "[거절코]": "https://media.discordapp.net/attachments/1526672551219036263/1526672857126408324/13_RM.png?ex=6a57e065&is=6a568ee5&hm=c6126a2a00eee67854313d00fd842881c028bb9cedd87e46098bedae7afb3519&=&format=webp&quality=lossless",
    "[메롱]": "https://media.discordapp.net/attachments/1526672551219036263/1526672857604821194/14_RM.png?ex=6a57e065&is=6a568ee5&hm=f5400b25ff74aa2e55a402aa1796b22ba326ba87ab7ca605b647319e69ae9db8&=&format=webp&quality=lossless",
    "[찌르기거부]": "https://media.discordapp.net/attachments/1526672551219036263/1526672857936040097/15_RM.png?ex=6a57e065&is=6a568ee5&hm=0b1e3368b451d4c6dbecb9f62ac9544feb00bef0fd9b627a2fe1b572f7dc9232&=&format=webp&quality=lossless",
    "[찌르기]": "https://media.discordapp.net/attachments/1526672551219036263/1526672858309202041/16_RM.png?ex=6a57e065&is=6a568ee5&hm=7fbb0109c16fd62545d936f76a8317d5b91652db499ec246ba69b96f3a2b1aa0&=&format=webp&quality=lossless",
    "[신남!]": "https://media.discordapp.net/attachments/1526672551219036263/1526672882011476089/17_RM.png?ex=6a57e06b&is=6a568eeb&hm=0ce9fec978cf5e69f11ee491a1042fa5ce366c2b9aa11a756442e68b64e9ee58&=&format=webp&quality=lossless",
    "[항해!]": "https://media.discordapp.net/attachments/1526672551219036263/1526672882552541387/18_RM.png?ex=6a57e06b&is=6a568eeb&hm=e43c691242e1910a997a7743459e280d0e3c1626e0d2c5931eb00f53beab9d37&=&format=webp&quality=lossless",
    "[채집!]": "https://media.discordapp.net/attachments/1526672551219036263/1526672882888081660/19_RM.png?ex=6a57e06b&is=6a568eeb&hm=64b9885a8f945cd218bff624d7af1268a11bcb8663a8f678899564cb46f34809&=&format=webp&quality=lossless",
    "[사냥!]": "https://media.discordapp.net/attachments/1526672551219036263/1526672883336613908/20_RM.png?ex=6a57e06b&is=6a568eeb&hm=8369147cd9c344275b8abb44034ae68eeae2cea02b30951a66a3b1d8a5e49615&=&format=webp&quality=lossless",
    "[?]": "https://media.discordapp.net/attachments/1526672551219036263/1526672883739525150/21_RM_v01.png?ex=6a57e06b&is=6a568eeb&hm=c5d76f0f416a00063ef7205009dcd8da077f5e95ba225df00ae35d62a75ceedb&=&format=webp&quality=lossless",
    "[숨바꼭질]": "https://media.discordapp.net/attachments/1526672551219036263/1526672884062228510/22_RM.png?ex=6a57e06b&is=6a568eeb&hm=bdad934918997d0c52ff2756bbe67aa4c958c3061c8e1082d36eaf589bd9b52d&=&format=webp&quality=lossless",
    "[어째해요]": "https://media.discordapp.net/attachments/1526672551219036263/1526672884490309843/23_RM.png?ex=6a57e06b&is=6a568eeb&hm=6495f81860ea9d5e50f43cfa56eaac87b90552cd058c44619b6804be3a26527f&=&format=webp&quality=lossless",
    "[몰라]": "https://media.discordapp.net/attachments/1526672551219036263/1526672884796489851/24_RM.png?ex=6a57e06b&is=6a568eeb&hm=87e242ceaa184de1610c47c642a9477c838bed821a4d8cb467fcf9f5c8721f55&=&format=webp&quality=lossless",
    "[모코코]": "https://media.discordapp.net/attachments/1526672551219036263/1526672885106610280/25_RM.png?ex=6a58896c&is=6a5737ec&hm=8e38c330616462ea3afd80a8d2f8b2400a84b3e0a741ef8aab62be229ae9af33&=&format=webp&quality=lossless",
    "[앙녕]": "https://media.discordapp.net/attachments/1526672551219036263/1526672899891789904/26_RM.png?ex=6a58892f&is=6a5737af&hm=2072139374f6ebf9996cb99a902d9702fef91296e2deead91a054ab6d177912a&=&format=webp&quality=lossless",
    "[놀자]": "https://media.discordapp.net/attachments/1526672551219036263/1526672900197843004/27_RM.png?ex=6a58892f&is=6a5737af&hm=6437007c671cecb7c64a4a8a5a414592ad9e2ee004d984605a8d9585e26a257e&=&format=webp&quality=lossless",
    "[???]": "https://media.discordapp.net/attachments/1526672551219036263/1526672900483059874/28_RM.png?ex=6a58892f&is=6a5737af&hm=c3e5196bf617c4428d9f05c7a9ec4d508542992ec820b1652d0681368c4e83dd&=&format=webp&quality=lossless",
    "[선물]": "https://media.discordapp.net/attachments/1526672551219036263/1526672900797759659/29_RM.png?ex=6a58892f&is=6a5737af&hm=9d7ecab4f5683e2bf65492977ea3c7fbc84fb0c42ca3af0a24c74cc656d51b0d&=&format=webp&quality=lossless",
    "[고민]": "https://media.discordapp.net/attachments/1526672551219036263/1526672901099618324/30_RM.png?ex=6a58892f&is=6a5737af&hm=8b601fed0523dc67006c162663bd5375578f6e1bd25254b746d08cae401472ad&=&format=webp&quality=lossless",
    "[버그]": "https://media.discordapp.net/attachments/1526672551219036263/1526672901397418144/31_RM.png?ex=6a58892f&is=6a5737af&hm=ccc0583a9e92538bf2c876b7228c296e85ac444b562df2cac9687fa8662ada1e&=&format=webp&quality=lossless",
    "[하트투척]": "https://media.discordapp.net/attachments/1526672551219036263/1526672901737283714/32_RM.png?ex=6a58892f&is=6a5737af&hm=4a191817f64fd4b064a5f0d91709cdd91e503fc34821aacc75195d6d976a7e83&=&format=webp&quality=lossless",
    "[안녕2]": "https://media.discordapp.net/attachments/1526672551219036263/1526672902051725502/33_RM.png?ex=6a588930&is=6a5737b0&hm=b404a473fcbb6481d3db2716cddf99331712a25cc28b9604264ea75bce708324&=&format=webp&quality=lossless",
    "[편지]": "https://media.discordapp.net/attachments/1526672551219036263/1526672902353584180/34_RM.png?ex=6a588930&is=6a5737b0&hm=93c6556255a4a679634ad316a259317401072cf13fe2cab1eca061c50f9b1e8e&=&format=webp&quality=lossless",
    "[좋아요모코코]": "https://media.discordapp.net/attachments/1526672551219036263/1526672940450582628/03.gif?ex=6a588939&is=6a5737b9&hm=eadc36f1d335f708d395dd061b1c6aa83bc23861106c42f5c3e9aa3744ba27d0&=",
    "[ㄹㅇ?]": "https://media.discordapp.net/attachments/1526672551219036263/1526672940765282445/04.gif?ex=6a588939&is=6a5737b9&hm=33d4567e7a631207e531a842659978f860dbe94f63191716af306c99251fd3b2&=",
    "[방방]": "https://media.discordapp.net/attachments/1526672551219036263/1526672942719701192/09.gif?ex=6a588939&is=6a5737b9&hm=224b7019cf0a1ea6dc46457dc8cb472ec92b83a97ed867e08e59c3f4a77551b1&=",
    "[ㅋㅋㅋㅋ]": "https://media.discordapp.net/attachments/1526672551219036263/1526672931789209793/01.gif?ex=6a588937&is=6a5737b7&hm=2c514bc932e94d8014a2d6809d9dd97d0f0d6381657fcf37d41a59093c4231f1&=",
    "[두렵다]": "https://media.discordapp.net/attachments/1526672551219036263/1526672951682924585/18.png?ex=6a58893b&is=6a5737bb&hm=6b62d5397c689104351f7705a823aea3a0ced9fde54e6c40763ac6e7c1c2220f&=&format=webp&quality=lossless",
    "[헤헷]": "https://media.discordapp.net/attachments/1526672551219036263/1526672953050136667/12.gif?ex=6a58893c&is=6a5737bc&hm=d4c8457d87fba9b90041d64ca8ec6102a8c4bad3e271a6feaca689335e727b8f&=",
    "[이번만]": "https://media.discordapp.net/attachments/1526672551219036263/1526672953637474467/13.gif?ex=6a58893c&is=6a5737bc&hm=86889c41584aaeb79ead26d49c419e9236152e8692cc1d40ffd43b4120f6b202&=",
    "[때찌]": "https://media.discordapp.net/attachments/1526672551219036263/1526672954191118578/14.gif?ex=6a58893c&is=6a5737bc&hm=a7e00c9e3f8a0b5cd812e747cd0c18e7f1930dbba00e9daa447cc66c4584850e&=",
    "[미안]": "https://media.discordapp.net/attachments/1526672551219036263/1526672954677788703/15.gif?ex=6a58893c&is=6a5737bc&hm=42a9ed2b81f841e550b66b1c34a5cd595133279fdcfc5807d75d503bdc0accf1&=",
    "[슬퍼]": "https://media.discordapp.net/attachments/1526672551219036263/1526672955189235752/16.gif?ex=6a58893c&is=6a5737bc&hm=324d2e1cf8b6bddcdd11868190754b9834a2d06415740fa066323702f8e1c38b&=",
    "[주먹]": "https://media.discordapp.net/attachments/1526672551219036263/1526672977796530327/23.gif?ex=6a588942&is=6a5737c2&hm=c41aad50920947277cd9af3380e10f0a5b8047a209fdd8326112fc4d3e1b98c9&=",
    "[ㅇㅇ]": "https://media.discordapp.net/attachments/1526672551219036263/1526672991256183014/29.gif?ex=6a588945&is=6a5737c5&hm=3f04ebeb13000f75a441806b82a68e7a1b95a4994e18969ada7fab87c03390b9&=",
    "[ㄴㄴ]": "https://media.discordapp.net/attachments/1526672551219036263/1526672991667097600/30.gif?ex=6a588945&is=6a5737c5&hm=f606990e51b5f61317d9646737333f06eb9e8688deab6735e9de86a06b00130c&=",
    "[FLEX]": "https://media.discordapp.net/attachments/1526672551219036263/1526672993097482331/33.gif?ex=6a588945&is=6a5737c5&hm=38b0ebd26a4e8d4f87d4b661724a322cea7edf6dd2c490e3ce0e1ebdb5ff6b62&=",
    "[날라차기]": "https://media.discordapp.net/attachments/1526672551219036263/1526673088476086363/01_.png?ex=6a58895c&is=6a5737dc&hm=92e218ac8d06feccf53c032a2e16c1e678ccf14394e5afa50cbec6a874c29d4d&=&format=webp&quality=lossless",
    "[꺄꺄룽]": "https://media.discordapp.net/attachments/1526672551219036263/1526673090866839572/04_.png?ex=6a58895d&is=6a5737dd&hm=9d750b97ff38cfb48331e53188902c831bf5fd5c7b9fa52e26d96bbfa062bdf8&=&format=webp&quality=lossless",
    "[머쓱]": "https://media.discordapp.net/attachments/1526672551219036263/1526673099737665648/07_.png?ex=6a58895f&is=6a5737df&hm=a91b56d8746abb92debd67c9093ba5106bb0b40765c116fffb4e1c420e156d75&=&format=webp&quality=lossless",
    "[짝짝코]": "https://media.discordapp.net/attachments/1526672551219036263/1526673339886862397/01__22__02.png?ex=6a588998&is=6a573818&hm=c924938c1722200b80ef37fea83f8f07a33d4339d8f866bd0ff86c2592f000ee&=&format=webp&quality=lossless",
    "[야무치]": "https://media.discordapp.net/attachments/1526672551219036263/1526900903532171294/10.gif?ex=6a58b4c7&is=6a576347&hm=4ff8e6ede444c5c6103544b8ff6e9b7ce7ee68e1093a9e2197c4f32ccdf628cd&=",
    "[암수끝]": "https://media.discordapp.net/attachments/1526672551219036263/1526900903926300683/1.gif?ex=6a58b4c7&is=6a576347&hm=6a831a161efc2fd3a70748ff4594e548bb5b5cb168c1a1e40b4df6df65f918c2&=",
    "[도움요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900904236941333/2.gif?ex=6a58b4c8&is=6a576348&hm=cce718eb3eee3f9603a93616cb4cf48e0e36dbb99766c66eb5531287609055f4&=",
    "[도잉요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900904509575269/3.gif?ex=6a58b4c8&is=6a576348&hm=aecd9d0df2e8a14ce148322162516221a0b684399a31674f8b4fc17dd083753d&=",
    "[저요요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900904832270347/4.gif?ex=6a58b4c8&is=6a576348&hm=ea0aefdb50eb312349af719990e2566b3b4059aea3dec77c3497e7d2f879133a&=",
    "[뿌듯요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900905230995546/5.gif?ex=6a58b4c8&is=6a576348&hm=8586154c5b92292e3f1f4d3b0d4d65f099d41158ca0dfe52ccedbda474814958&=",
    "[미안요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900905994092606/6.gif?ex=6a58b4c8&is=6a576348&hm=6939128c5472809f5921759adaf1eafabd28685a22c5f7a46c1074da95c999cf&=",
    "[짜증]": "https://media.discordapp.net/attachments/1526672551219036263/1526900906308669592/7.gif?ex=6a58b4c8&is=6a576348&hm=797dfa8960c74fc562cf15d9fb82947824e987726b6dd016a446aace3bad4014&=",
    "[시무룩]": "https://media.discordapp.net/attachments/1526672551219036263/1526900906686283776/8.gif?ex=6a58b4c8&is=6a576348&hm=1c0d6e994548fe483b7587a5d81545096efb4cdf0683d68d0b032be03a8caf33&=",
    "[눈치]": "https://media.discordapp.net/attachments/1526672551219036263/1526900907067838576/9.gif?ex=6a58b4c8&is=6a576348&hm=950628d9ed4d9f59fda05139b4b72b9d68cbabdb2d81dce827ce4b38352e3cfc&=",
    "[이를거임!]": "https://media.discordapp.net/attachments/1526672551219036263/1526900927796084756/16.gif?ex=6a58b4cd&is=6a57634d&hm=b548760fe694e7dae39f0678223e1d85b39393b81a6b238d2ec0284fb46d08d0&=",
    "[메롱]": "https://media.discordapp.net/attachments/1526672551219036263/1526900928060588072/11.gif?ex=6a58b4cd&is=6a57634d&hm=c627aba0e6ce83aebbf1eca5a437805e12f760d6e1b92ed0af60618de2042b31&=",
    "[ㅊㅋ]": "https://media.discordapp.net/attachments/1526672551219036263/1526900928400330862/12.gif?ex=6a58b4cd&is=6a57634d&hm=983c1fa5e601a91d0892a30ebbcb43f07fb0227040dff2dc47173eb91c5f9f50&=",
    "[한잔해]": "https://media.discordapp.net/attachments/1526672551219036263/1526900928714637453/13.gif?ex=6a58b4cd&is=6a57634d&hm=1e4d149780219172f5d8245c8a23575762addce5eee1184abc518e7351e50ac2&=",
    "[배고파]": "https://media.discordapp.net/attachments/1526672551219036263/1526900929004306554/14.gif?ex=6a58b4cd&is=6a57634d&hm=564f7a168c72f88a2a7eab6d12016164d4f389ef128fe2bc2300125cd4ff9daa&=",
    "[관람요즈콘]": "https://media.discordapp.net/attachments/1526672551219036263/1526900929293717575/15.gif?ex=6a58b4cd&is=6a57634d&hm=7ab4311418bb48e52d3add04ee51d868414f662768a3012830b110a8937bf191&="
}

# =========================
# 기본 이벤트 처리
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(CubeView())
    print(f"✅ 로스트아크 통합 봇 로그인 완료: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return

    if message.content in STICKER_MAP:
        image_url = STICKER_MAP[message.content]
        embed = discord.Embed(color=0x2B2D31)
        embed.set_image(url=image_url)
        await message.channel.send(embed=embed)
        return

    await bot.process_commands(message)

@bot.command()
async def 인증패널(ctx): 
    await ctx.send(embed=discord.Embed(title="로스트아크 길드 인증", color=0x2B2D31), view=VerifyView(), delete_after=900)

@bot.command()
async def 큐브계산기(ctx): 
    await ctx.send(embed=discord.Embed(title="🎲 큐브 매칭", color=0x2B2D31), view=CubeView(), delete_after=900)

bot.run(DISCORD_TOKEN)
bot.run(DISCORD_TOKEN)
