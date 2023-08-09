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

def app():
    st.set_page_config(
        page_title="Hani Audio Article",
        page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/1024px-Speaker_Icon.svg.png"
    )
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/1024px-Speaker_Icon.svg.png", width=150)
    st.title("Hani Audio Article")
    st.subheader("한겨레 기사 URL을 넣으면 해당 기사를 음성으로 읽어줍니다.")
    hani_url = st.text_input(label="한겨레 기사 웹주소를 넣어주세요.", placeholder="https://www.hani.co.kr/arti/politics/politics_general/1091588.html", key="hani_url",)
    
    # session_state 설정
    if 'tts_button' not in st.session_state:
        st.session_state.tts_button = False
    if 'mp3_button' not in st.session_state:
        st.session_state['mp3_button'] = False
    if 'sub_button' not in st.session_state:
        st.session_state['sub_button'] = False

    if st.session_state['tts_button'] == True:
        st.session_state['sub_button'] = True
        st.session_state['mp3_button'] = True
    else:
        if st.button("새로운 기사로 다시 시도하기"):
            st.session_state['mp3_button'] = False
            st.session_state['sub_button'] = False

    tts_button = st.button("오디오 기사 만들기", key='tts_button')
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
    volume = str(volume_value) + '%'
    if volume_value >= 0:
        volume = '+' + str(volume_value) + '%'
    
    if tts_button:
        with st.spinner("오디오 기사를 생성하고 있어요... 🧐"):
            text = get_article(hani_url)
            audio_filename, sub_filename, filehead = make_filename(hani_url)
            try:
                # asyncio.run(amain(text, voice, rate, volume, audio_filename))
                asyncio.run(amain(text, voice, rate, volume, audio_filename, sub_filename))
                with open(audio_filename, "rb") as f:
                    mp3_file = f.read()
                st.audio(mp3_file, format='audio/mp3')
                st.success("오디오 기사 생성 완료! 🥳")
                st.write("원본 기사: ", hani_url)
                # st.write("오디오 재생기 옆 '⋮' 버튼을 눌러 오디오 파일을 내려받을 수 있습니다.(확장자를 '.mp3'로 지정)")
                st.download_button(
                    label="오디오 파일(MP3) 내려받기",
                    data=mp3_file,
                    file_name=filehead + '.mp3',
                    mime='audio/mp3',
                    key='mp3_button'
                )
                
                with open(sub_filename, "rb") as f:
                    st.download_button(
                        lable="자막 파일(VTT) 내려받기", 
                        data=f, 
                        file_name=filehead + '.vtt', 
                        key='sub_button'
                    )
            except Exception as e:
                st.error(e)

if __name__ == "__main__":
    app()
