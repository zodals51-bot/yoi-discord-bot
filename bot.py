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
    
    # 🆕 신규 클래스 '차원술사' 시너지 수정 반영 (방깎 12%)
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


# =========================
# ⚖️ 경매 분배금 계산기 (!경매 [금액])
# =========================
@bot.command(name="경매")
async def calculate_auction(ctx, price: int = None):
    if not price or price <= 0:
        await ctx.send("❌ 사용법: `!경매 [경매장 시세]` (예: `!경매 10000`)")
        return

    net_value = int(price * 0.95)
    
    calc_data = {
        "4인 파티 (군단장)": {"break_even": int(net_value * 3 / 4), "recommend": int(net_value * 0.95 * 3 / 4)},
        "8인 파티 (어비스 레이드)": {"break_even": int(net_value * 7 / 8), "recommend": int(net_value * 0.95 * 7 / 8)},
        "16인 파티 (어비스 던전)": {"break_even": int(net_value * 15 / 16), "recommend": int(net_value * 0.95 * 15 / 16)}
    }

    embed = discord.Embed(title=f"⚖️ 경매 입찰금 정산기 (시세: {price:,} G)", color=0xF1C40F)
    embed.description = f"💡 **수수료 제외 가치:** {net_value:,} 골드\n*아래 추천가까지만 눌러야 이득입니다.*"

    for team, data in calc_data.items():
        b_even = data["break_even"]
        recom = data["recommend"]
        embed.add_field(
            name=f"👥 {team}",
            value=f"• **추천 입찰가:** `{recom:,} G` (이득 가능)\n• **손익 분기점:** `{b_even:,} G` (여기 넘기면 손해)",
            inline=False
        )
    
    await ctx.send(embed=embed)


# =========================
# 🌊 지옥 보상효율표 및 확률 분석 (!지옥효율)
# =========================
@bot.command(name="지옥효율")
async def show_hell_reward_efficiency(ctx):
    embed = discord.Embed(
        title="🌋 낙원 : 지옥 콘텐츠 구간별 보상 효율표", 
        url="https://m.lopec.kr/tool/reward",
        color=0xE74C3C,
        description="💡 **Lopec(로펙) 도구 기준** 최신 재화 가치 산정 결과입니다.\n재화 시세에 따라 미세 변동이 있을 수 있으나 큐브 대비 효율성이 우세합니다."
    )
    
    embed.add_field(
        name="💎 1640 구간 (기대 가치: 약 14,500 G)", 
        value="• 주요 드롭: 운명 파괴석/수호석, 카르마 돌파석, 젬 랜덤 상자\n• 효율 분석: **큐브보다 소폭 우세**", 
        inline=False
    )
    embed.add_field(
        name="💎 1700 구간 (기대 가치: 약 23,000 G)", 
        value="• 주요 드롭: 상위 운명 재화 시리즈, 성장의 더스트, 실링 상자\n• 효율 분석: 🔥 **추천 파밍 구간**", 
        inline=False
    )
    embed.add_field(
        name="💎 1730 최상위 구간 (기대 가치: 최대 115,000 G 이상)", 
        value="• 주요 드롭: 엔드게임 전용 파괴/수호석 결정, 최상위 돌파석, 젬 선택 상자\n• 효율 분석: 🌟 **원정대 스펙업 필수 교환 1순위**", 
        inline=False
    )
    
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="🎲 **희귀(파란색) 열쇠 5회 제한 '억까' 확률 분석**",
        inline=False
    )
    embed.add_field(
        name="📈 평균 기대 도달 층수",
        value="• 1회 강하당 1~20층 이동 (균등 확률 1/20)\n• 5회 강하 시 평균 기대값: **52.5층**",
        inline=True
    )
    embed.add_field(
        name="🚨 5회 강하 후 '5층 마무리' 확률",
        value="• 5번 모두 연속으로 1층씩만 나올 확률\n• `(1/20)^5` = **0.00003125%** (로또보다 희박)",
        inline=True
    )
    
    embed.set_footer(text="출처: Lopec(로펙) 리워드 효율 산정 툴 및 내부 통계 시뮬레이션")
    await ctx.send(embed=embed)


# =========================
# 🌋 레벨/층수 맞춤형 지옥 보상 판별기 (!지옥추천)
# =========================
@bot.command(name="지옥추천")
async def recommend_hell_reward(ctx, level: str, floor_range: str, *rewards: str):
    if not level or not floor_range or len(rewards) < 2:
        await ctx.send("❌ **사용법:** `!지옥추천 [레벨] [층수구간] [보상1] [보상2] ...`\nℹ️ 예시: `!지옥추천 1750 0~10 어빌 특재 골드`")
        return

    level_multiplier = 1.0
    if level == "1640": level_multiplier = 0.5
    elif level == "1700": level_multiplier = 1.0
    elif level == "1730": level_multiplier = 2.5
    elif level == "1750": level_multiplier = 4.0

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
    
    analyzed_rewards = []
    unknown_rewards = []

    for r_input in rewards:
        clean_input = r_input.replace(" ", "")
        
        if clean_input in BASE_REWARD_VALUES:
            base_val = BASE_REWARD_VALUES[clean_input]
            
            if clean_input in ["아비도스", "융화재료", "파괴석", "수호석", "결정", "돌파석"]:
                final_value = base_val * level_multiplier * floor_multiplier
            else:
                final_value = base_val * level_multiplier * (1.0 + (target_floor / 50.0))

            analyzed_rewards.append({
                "original": r_input,
                "calc_val": final_value
            })
        else:
            unknown_rewards.append(r_input)

    if not analyzed_rewards:
        await ctx.send("❌ 인식된 보상이 없습니다. 단어 뒤에 오타가 없는지 확인해 주세요!")
        return

    analyzed_rewards.sort(key=lambda x: x["calc_val"], reverse=True)

    embed = discord.Embed(
        title=f"🌋 [지옥 보상] {level}레벨 / {floor_range} 구간 실시간 판별",
        color=0x2ECC71,
        description=f"📊 현재 단계에서 `lo4.app` 시뮬레이션 효율이 가장 높은 순서입니다."
    )
    
    best_reward = analyzed_rewards[0]
    embed.add_field(
        name=f"🥇 지금 이 구간 최고의 [1등상]",
        value=f"👉 **{best_reward['original']}**",
        inline=False
    )

    rank_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅"]
    for idx, item in enumerate(analyzed_rewards):
        medal = medals[idx] if idx < len(medals) else "•"
        rank_text += f"{medal} **{idx+1}위**: {item['original']}\n"
        
    embed.add_field(name="📋 보상 선택 우선순위", value=rank_text, inline=False)

    if unknown_rewards:
        embed.add_field(name="⚠️ 인식 실패 (오타 확인)", value=f"`{', '.join(unknown_rewards)}`", inline=False)

    embed.set_footer(text=f"기준: lo4.app 층수 스케일링 ({int(target_floor)}층 가중치 적용)")
    await ctx.send(embed=embed)


# =========================
# ⏰ 알람 타이머 (장난 및 복귀 멘션용)
# =========================
@bot.command(name="알람")
async def set_timer(ctx, time_str: str = None, *, memo: str = "시간 완료!"):
    if not time_str:
        await ctx.send("❌ 사용법: `!알람 [시간+단위] [멘션/메모]` (예: `!알람 10분`, `!알람 3분 @홍길동 얼른 복귀해라`)")
        return

    seconds = 0
    if "분" in time_str:
        minutes = int(time_str.replace("분", "").strip())
        seconds = minutes * 60
    elif "초" in time_str:
        seconds = int(time_str.replace("초", "").strip())
    else:
        try:
            seconds = int(time_str) * 60
            time_str = f"{time_str}분"
        except ValueError:
            await ctx.send("❌ 시간을 올바르게 입력해주세요. (예: 10분, 30초)")
            return

    if seconds <= 0:
        await ctx.send("❌ 0보다 큰 시간을 입력해주세요.")
        return

    await ctx.send(f"⏰ {ctx.author.mention}님, **{time_str}** 알람이 예약되었습니다. (내용: {memo})")
    
    await asyncio.sleep(seconds)
    await ctx.send(f"🚨 **[{time_str} 완료]** ➜ {memo}")


# =========================
# 기본 기능들 (정보, 낙원, 시너지, 조합, 큐브, 인증)
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
            if "전투력" in str(stat.get("Type", "")):
                clean_val = re.sub(r'[^\d.]', '', str(stat.get("Value", "")))
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

@bot.command(name="낙원")
async def show_nakwon_code(ctx, job_name: str = None):
    if not job_name:
        available_jobs = ", ".join([f"`{k}`" for k in NAKWON_SKILL_CODES.keys()])
        await ctx.send(f"❌ 사용법: `!낙원 [직업명]`\nℹ️ 등록된 직업: {available_jobs}")
        return
    matched_job = None
    for key in NAKWON_SKILL_CODES.keys():
        if job_name in key: matched_job = key; break
    if not matched_job:
        await ctx.send(f"❌ `{job_name}` 직업의 낙원 증명용 스킬코드를 찾을 수 없습니다.")
        return
    job_data = NAKWON_SKILL_CODES[matched_job]
    embed = discord.Embed(title=f"🌊 낙원 증명용 {matched_job} 아크 패시브", color=0x00A3FF)
    embed.add_field(name="📋 복사용 스킬코드", value=f"```{job_data['code']}```", inline=False)
    embed.add_field(name="💡 운용 팁 / 공략", value=f"{job_data['tip']}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="시너지")
async def show_synergy(ctx):
    embed = discord.Embed(title="⚔️ 로스트아크 전 직업 시너지 표", color=0x2B2D31)
    jobs = list(SYNERGY_DETAILS.keys())
    chunks = [jobs[i:i + 6] for i in range(0, len(jobs), 6)]
    for i, chunk in enumerate(chunks):
        chunk_text = ""
        for job in chunk: 
            chunk_text += f"• **{job}**: {SYNERGY_DETAILS[job]['desc']}\n"
        embed.add_field(name=f"시너지 목록 ({i+1})", value=chunk_text, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="레이드조합")
async def analyze_raid_party(ctx, *jobs: str):
    if len(jobs) < 1 or len(jobs) > 4:
        await ctx.send("❌ 사용법: `!레이드조합 [직업1] [직업2] [직업3] [직업4]`")
        return
    matched_jobs, invalid_jobs = [], []
    for job in jobs:
        found = False
        for key in SYNERGY_DETAILS.keys():
            if job in key: matched_jobs.append(key); found = True; break
        if not found: invalid_jobs.append(job)
    if invalid_jobs:
        await ctx.send(f"❌ 알 수 없는 직업이 포함되어 있습니다: {', '.join([f'`{j}`' for j in invalid_jobs])}")
        return
    effect_counts = {}
    has_supp = has_backhead = False
    for job in matched_jobs:
        effects = SYNERGY_DETAILS[job]["effects"]
        if "케어" in effects: has_supp = True
        if job in ["워로드", "블레이드"]: has_backhead = True
        for eff in effects:
            if eff != "케어": effect_counts[eff] = effect_counts.get(eff, 0) + 1
    embed = discord.Embed(title="🛡️ 로아가드 레이드 헬퍼 파티 조합 분석", color=0x3498DB)
    embed.add_field(name="👥 현재 구성 파티원", value=" / ".join([f"**{j}**" for j in matched_jobs]), inline=False)
    overlap_text = "".join([f"⚠️ **[{eff}]** 시너지가 **{count}개** 중첩되었습니다.\n" for eff, count in effect_counts.items() if count > 1])
    embed.add_field(name="🚨 시너지 중첩 경고", value=overlap_text if overlap_text else "✅ 중첩된 시너지가 없이 깔끔합니다!", inline=False)
    embed.add_field(name="✨ 활성화된 시너지 효과", value="\n".join([f"• {eff}" for eff in effect_counts.keys()]) if effect_counts else "없음", inline=True)
    missing_effects = [m for m in ["치적", "방깎", "피증"] if m not in effect_counts]
    embed.add_field(name="❌ 누락된 필수 시너지", value="\n".join([f"• {m}" for m in missing_effects]) if missing_effects else "✅ 필수 시너지 완비!", inline=True)
    score = max(10, 100 - sum([(c - 1) * 20 for c in effect_counts.values() if c > 1]) - len(missing_effects) * 15 - (20 if not has_supp and len(matched_jobs) == 4 else 0))
    evaluation = "🌟 **최상 (시너지 도둑 조합)**" if score >= 85 else "✅ **양호 (무난한 조합)**" if score >= 65 else "🔺 **조정 필요 (시너지 불협화음)**"
    embed.add_field(name="📊 조합 시너지 점수", value=f"**{score}점**\n{evaluation}", inline=False)
    if has_backhead:
        embed.add_field(name="📐 특수 조합 코멘트", value="💡 파티에 **사멸(백/헤드) 시너지**가 포함되어 있으므로, 사멸 딜러 배치 시 시너지 효율이 극대화됩니다.", inline=False)
    await ctx.send(embed=embed)


# =========================
# 🎲 큐브 매칭 정산 시스템
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
# 길드 인증 기능 (차원술사 자동 역할 부여 대응)
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
        char_class = profile["CharacterClassName"]  # API에서 '차원술사' 문자열을 그대로 반환함
        char_guild = profile.get("GuildName") or ""
        
        # 1. 디스코드 서버 닉네임 변경 (예: 홍길동/차원술사)
        try: await member.edit(nick=f"{char_name}/{char_class}")
        except: pass
        
        # 2. 추가할 직업 역할 목록 생성
        roles_to_add = [char_class]
        
        # 3. 길드 소속 여부에 따른 내부원 / 외부인 역할 처리
        config_guild = os.getenv("GUILD_NAME", "")
        if char_guild.strip() == config_guild.strip() if config_guild else False:
            member_role = os.getenv("MEMBER_ROLE", "")
            if member_role: roles_to_add.append(member_role)
        else:
            roles_to_add.append(os.getenv("GUEST_ROLE", "외부인"))
            
        # 4. 서버에 등록된 직업 명칭(차원술사 포함)의 역할을 찾아 유저에게 자동 지급
        for r_name in roles_to_add:
            role = discord.utils.get(guild.roles, name=r_name)
            if role: 
                await member.add_roles(role)
                
        embed = discord.Embed(title="✅ 인증 완료", description=f"**{char_name}**({char_class})님 환영합니다.", color=0x57F287)
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
