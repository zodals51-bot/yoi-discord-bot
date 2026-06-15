import os
from dotenv import load_dotenv

# .env 파일에 숨겨진 환경 변수들을 불러옵니다.
load_dotenv()

# 보안이 필요한 비밀키들은 서버의 .env 파일에서 쏙 쏙 찾아옵니다.
DISCORD_TOKEN = os.getenv("MTUxNTY5MjE5MjIyNjg3MzQxNA.GDemzH.30kxFgswMlFi7AIZy0r7S4I8wFy2Qj1b6kLTaI")
LOSTARK_API_KEY = os.getenv("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyIsImtpZCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyJ9.eyJpc3MiOiJodHRwczovL2x1ZHkuZ2FtZS5vbnN0b3ZlLmNvbSIsImF1ZCI6Imh0dHBzOi8vbHVkeS5nYW1lLm9uc3RvdmUuY29tL3Jlc291cmNlcyIsImNsaWVudF9pZCI6IjEwMDAwMDAwMDA1OTE4MzIifQ.O5C8ZSZwRSmR2HavFrtFzsWQ6ut1Ua9ZovpZ7FXj3eZYGcvJhHduMLkid-dO9dhAbhFWmciK9tOzlQviRtuRk7SUB8r0A_MrZJBs2JvjWx6BkG-kDJXgAq7h_q3oUKwDNLzJN2r02drz_7ewUwb4vzvfWDFbI_FfUgCD6VbsAki6S8T9R1eumb6BA3L-cuWg-GDhSb7v1bKW59e--M62JReaJdGR8CYWbQDsKvDN5uAOQd3Jl3wQLdeG7yUEo_xSZC5dtOttwd3BPVycLQccb0_PRrUKiXxdXs7csOyYdFgHZ89T7P1xAKminTGWR1QCEvnQ6fgLHJFBb2ntNLL8WQ")

# 공개되어도 상관없는 일반 설정들은 그대로 유지합니다.
GUILD_NAME = "요이"
WAIT_ROLE = "인증대기"
MEMBER_ROLE = "길드원"
