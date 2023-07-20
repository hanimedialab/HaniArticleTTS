import asyncio
import edge_tts
import os
import requests
from bs4 import BeautifulSoup
import time
import streamlit as st
import tempfile as tf

# 기사 본문 뽑기
def get_article(hani_url):
    res = requests.get(hani_url)
    soup = BeautifulSoup(res.text, 'lxml')
    article_body = soup.find('div', attrs={'class': 'text'}).text.strip()
    # print(article_body)
    return article_body

# 임시 폴더 생성
def create_temp_dir():
    # Create a temporary directory
    set_temp_dir = tf.TemporaryDirectory()
    temp_dir = set_temp_dir.name + "/"
    # 디렉터리 접근 권한 설정
    os.chmod(temp_dir, 0o700)
    return temp_dir

def make_filename(hani_url):
    temp_dir = create_temp_dir()
    filehead = hani_url.split('/')[-1].split('.')[0]
    filename = os.path.join(temp_dir + filehead + ".mp3")
    return filename


async def amain(text, voice, rate, volume, filename):
    """Main function"""
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    await communicate.save(filename)

def make_mp3(text, voice, filename):
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(amain(text, filename))
    finally:
        loop.close()

def app():
    st.set_page_config(
        page_title="Hani Audio Article",
        page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/1024px-Speaker_Icon.svg.png"
    )
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/1024px-Speaker_Icon.svg.png", width=150)
    st.title("Hani Audio Article")
    st.subheader("한겨레 기사 URL을 넣으면 해당 기사를 음성으로 읽어줍니다.")
    hani_url = st.text_input(label="한겨레 기사 웹주소를 넣어주세요.", placeholder="https://www.hani.co.kr/arti/politics/politics_general/1091588.html", key="hani_url",)
    tts_button = st.button("오디오 기사 만들기")
    # 목소리 선택
    voice_select = st.radio(
            "목소리를 선택하세요.",
            ('선희(여성)', '인준(남성)')
        )
    voices = {'선희(여성)': 'ko-KR-SunHiNeural', '인준(남성)': 'ko-KR-InJoonNeural'}
    voice = voices[voice_select]
    # 읽기 속도
    rate_value = st.slider(
        "읽기 속도",
        0, 30,
    )
    rate = '+' + str(rate_value) + '%'
    # 볼륨 조절
    volume_value = st.slider("볼륨 조절", -50, 50, 0)
    volume_value = str(volume_value) + '%'
    if volume_value >= 0:
        volume = '+' + str(volume_value) + '%'
        
    if tts_button:
        with st.spinner("오디오 기사를 생성하고 있어요... 🧐"):
            text = get_article(hani_url)
            filename = make_filename(hani_url)
            print("파일 위치: ", filename)
            try:
                asyncio.run(amain(text, voice, rate, volume, filename))
                print("mp3 : ", filename)
                with open(filename, "rb") as f:
                    mp3_file = f.read()
                st.audio(mp3_file, format='audio/mp3')
                st.success("오디오 기사 생성 완료! 🥳")
                st.write("오디오 재생기 오른쪽 ⋮ 를 눌러 mp3 파일을 내려받을 수 있습니다.")
                st.write("원본 기사: ", hani_url)
            except Exception as e:
                st.error(e)

if __name__ == "__main__":
    app()
