import asyncio
import edge_tts
import os
import streamlit as st
import tempfile as tf
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# 기사 본문 뽑기
def get_article(hani_url):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(ChromeDriverManager(version="latest").install(), options=options)
    driver.maximize_window()
    driver.get(hani_url)
    title = driver.find_element(By.XPATH, '//*[@id="renewal2023"]/h3').text
    try:
        subtitle = driver.find_element(By.XPATH, '//*[@id="renewal2023"]/h4').text
    except:
        subtitle = ""
    article_area = driver.find_elements(By.XPATH, '//*[@id="renewal2023"]/div[3]')
    articles = article_area[0].find_elements(By.TAG_NAME, 'p') 
    # print("제목: ", title)
    article_body = ""
    for article in articles:
        print(article.text)
        article_body += article.text + "\n"
    return {
        "title": title,
        "subtitle": subtitle,
        "article_body": article_body
    }

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
    audio_filename = os.path.join(temp_dir + filehead + ".mp3")
    sub_filename = os.path.join(temp_dir + filehead + ".vtt")
    return audio_filename, sub_filename, filehead

# 스트리밍 오디오/자막 파일 생성
async def amain(text, voice, rate, volume, audio_filename, sub_filename):
    # Main function
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    submaker = edge_tts.SubMaker()
    os.makedirs(os.path.dirname(audio_filename), exist_ok=True)
    with open(audio_filename, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    os.makedirs(os.path.dirname(sub_filename), exist_ok=True)
    with open(sub_filename, "w", encoding="utf-8") as file:
        file.write(submaker.generate_subs())

def app():
    # 세션 상태 가져오기
    if "audio_file" not in st.session_state:
        st.session_state.audio_file = None
    if "sub_file" not in st.session_state:
        st.session_state.sub_file = None
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
        0, 30, 10
    )
    rate = '+' + str(rate_value) + '%'
    # 볼륨 조절
    volume_value = st.slider("볼륨 조절", -50, 50, 0)
    volume = str(volume_value) + '%'
    if volume_value >= 0:
        volume = '+' + str(volume_value) + '%'
    
    if tts_button:
        with st.spinner("오디오 기사를 생성하고 있어요... 🧐"):
            article = get_article(hani_url)
            text = article['article_body']
            audio_filename, sub_filename, filehead = make_filename(hani_url)
            try:
                # asyncio.run(amain(text, voice, rate, volume, audio_filename))
                asyncio.run(amain(text, voice, rate, volume, audio_filename, sub_filename))
                with open(audio_filename, "rb") as f:
                    mp3_file = f.read()
                st.audio(mp3_file, format='audio/mp3')
                st.success("오디오 기사 생성 완료! 🥳")
                st.write("원본 기사: ", hani_url)
                # 오디오 파일과 자막 파일을 세션 상태에 저장
                st.session_state.audio_file = mp3_file
                st.session_state.sub_file = sub_filename
                # 세션 상태에 저장된 오디오 파일과 자막 파일을 사용
                if st.session_state.audio_file is not None:
                    st.audio(st.session_state.audio_file, format='audio/mp3')
                    st.download_button(
                        label="오디오 파일(MP3) 내려받기",
                        data=st.session_state.audio_file,
                        file_name=filehead + '.mp3',
                        mime='audio/mp3'
                    )
                if st.session_state.sub_file is not None:
                    with open(st.session_state.sub_file, "rb") as f:
                        st.download_button(
                            label="자막 파일(VTT) 내려받기", 
                            data=f, 
                            file_name=filehead + '.vtt'
                        )
            except Exception as e:
                st.error("오류가 발생했습니다.")
                st.error(e)

if __name__ == "__main__":
    app()
