import streamlit as st
import openai
from audiorecorder import audiorecorder
import numpy as np
import os
from datetime import datetime
from gtts import gTTS
import base64  # 음눤 파일을 재생하기 위한 패키지 추가

## 기능 구현 함수
def STT(audio, client):
    # 파일 저장
    filename = "input.mp3"
    wav_file = open(filename, "wb")
    wav_file.write(audio.tobytes())
    wav_file.close()
    
    # 음원 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용해 텍스트 얻기
    # transcript = openai.Audio.transcribe("whisper-1", audio_file)    # openai 0.28?
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file) # openai 1.xx
    audio_file.close()
    # 파일 삭제
    os.remove(filename)
    # return transcript["text"]
    print(transcript.text)
    return transcript.text

# ChatGPT에 답변 구하기
def ask_gpt(prompt, model, client):
    # response = openai.ChatCompletion.create(model=model, messages=prompt)  # openai 0.28
    response = client.chat.completions.create(model=model, messages=prompt)  # openai 1.xx
    # system_message = response["choices"][0]["message"]  # openai 0.28
    system_message = response.choices[0].message  # openai 1.xx
    # return system_message["content"]   ## openai 0.28
    print(system_message)
    return system_message.content   # openai 1.xx

# Text to Speech 음성 파일 재생
def TTS(response):
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)
    
    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True,)
    # 파일 삭제
    os.remove(filename)

#### 메인 함수 ####
def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide"
    )
    
    flag_start = False
    
    # 제목
    st.header("음성 비서 프로그램 header")
    
    # 구분선
    st.markdown("---")
    
    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 활용했습니다.
            - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
            - 답변은 OpenAI의 GPT모델을 활용했습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
            """
        )
        
        st.markdown("")
    
    # Session State 초기화
    if "chat"  not in st.session_state:
        st.session_state["chat"] = []
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in Korean."}]

    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = []
    
    # 사이드바 생성
    with st.sidebar:
        # Open AI API 키 입력받기
        API_KEY = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", value="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", type="password")
        # openai.api_key = "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"
        client = openai.OpenAI(api_key = API_KEY)   ## openai 1.x 버전에 맞는 코드
        
        st.markdown("---")        
        
        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="gpt 모델", options=["gpt-4", "gpt-3.5-turbo"])
        print(model)
        
        st.markdown("---")
        
        # 리셋 버튼 생성
        bt = st.button(label="초기화")
        if bt:
            # 리셋 코드
            print(bt)
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in Korean."}]
        
    # 기능 구현 공간
    col1, col2 = st.columns(2)    
    
    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if len(audio) > 0 and not np.array_equal(audio, st.session_state["check_audio"]):
            # 음성 재생
            st.audio(audio.tobytes())
            # 음원 파일에서 텍스트 추출
            question = STT(audio, client)
            
            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]
            # 질문 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}]
            # audio 버퍼를 확인하기 위해 오디오 정보 저장
            st.session_state["check_audio"] = audio
            flag_start = True
                        
        print(len(audio), audio)
        
    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")    
        if flag_start:
            # ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state["messages"], model, client)   
            
            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "system", "content": response}]
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]
            
            # 채팅 형식으로 시각화 하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
            
            # gTTS 를 활용하여 음성 파일 생성 및 재생
            TTS(response)
    
if __name__ == "__main__":
    main()
    