import os
from dotenv import load_dotenv

# .env 파일에 숨겨진 환경 변수들을 불러옵니다.
load_dotenv()

# 보안이 필요한 비밀키들은 서버의 .env 파일에서 쏙 쏙 찾아옵니다.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOSTARK_API_KEY = os.getenv("LOSTARK_API_KEY")

# 공개되어도 상관없는 일반 설정들은 그대로 유지합니다.
GUILD_NAME = "요이"
WAIT_ROLE = "인증대기"
MEMBER_ROLE = "길드원"
