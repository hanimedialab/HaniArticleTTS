import asyncio
import edge_tts
import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
import tempfile as tf

# 기사 본문 뽑기
def get_article(hani_url):
    res = requests.get(hani_url)
    soup = BeautifulSoup(res.text, 'lxml')
    article_area = soup.find('div', attrs={'class': 'text'})
    try:
        # 사진 설명 제거
        divs = article_area.find_all('div')
        for div in divs:
            div.decompose()
        # 중간 발문 제거
        spans = article_area.find_all('span')
        for span in spans:
            span.decompose()
    except:
        pass
    article_body = article_area.text.strip()
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
    audio_filename = os.path.join(temp_dir + filehead + ".mp3")
    sub_filename = os.path.join(temp_dir + filehead + ".vtt")
    return audio_filename, sub_filename, filehead

# 스트리밍 오디오/자막 파일 생성
async def amain(text, voice, rate, volume, audio_filename, sub_filename):
    """Main function"""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    async with communicate as session:
        async for chunk in session:
            with open(audio_filename, 'ab') as f:
                f.write(chunk)
            with open(sub_filename, 'a') as f:
                f.write('\n')
                f.write(chunk.text)

# Streamlit App
st.set_page_config(page_title="한겨레 기사 TTS", page_icon=":guardsman:", layout="wide")

st.title("한겨레 기사 TTS")

st.write("한겨레 기사 링크를 입력해주세요.")
hani_url = st.text_input("한겨레 기사 링크")

if hani_url:
    article_body = get_article(hani_url)
    st.write(article_body)

    if 'tts_button' not in st.session_state:
        st.session_state['tts_button'] = False
    if 'sub_button' not in st.session_state:
        st.session_state['sub_button'] = False

    if st.session_state['tts_button'] == False:
        st.session_state['sub_button'] = False
        st.session_state['tts_button'] = st.button("오디오 파일(mp3) 내려받기")
    else:
        if st.button("새로운 기사로 다시 시도하기"):
            st.session_state['tts_button'] = False
            st.session_state['sub_button'] = False
        else:
            st.session_state['sub_button'] = st.button("자막 파일(VTT) 내려받기")

    if st.session_state['tts_button'] == True and st.session_state['sub_button'] == True:
        voice = "ko-KR-SunHiNeural"
        rate = 0.5
        volume = 0.5

        audio_filename, sub_filename, filehead = make_filename(hani_url)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(amain(article_body, voice, rate, volume, audio_filename, sub_filename))

        st.write(f"{filehead}.mp3 파일이 다운로드되었습니다.")
        st.audio(audio_filename)
        st.write(f"{filehead}.vtt 파일이 다운로드되었습니다.")
        with open(sub_filename, 'r') as f:
            st.write(f.read())
