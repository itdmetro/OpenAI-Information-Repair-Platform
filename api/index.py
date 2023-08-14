from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT
#import speech_recognition及pydub套件
import speech_recognition as sr
# from pydub import AudioSegment
import openai
# import whisper
# import tempfile
# from google.cloud import speech_v1p1beta1 as speech
import requests
import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    # print("Request body: " + body)
    # app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def google_custom_search(api_key, cse_id, num_results, query):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": num_results
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    result_list = []
    # if False:
    if "items" in data:
        result_list.append("我的連網能力還不是很厲害，但以下有相關網站可供參考：")
        # print("我的連網能力還不是很厲害，但以下有相關網站可供參考：")
        # for item in data["items"]:
        for i in range(len(data["items"])):
            title = data["items"][i]["title"]
            link = data["items"][i]["link"]
            result_list.append(f"{title}")
            result_list.append(f"{link}")
            # result_list.append(f"標題{i+1}： {title}")
            # result_list.append(f"連結{i+1}： {link}")
            # print(f"標題： {title} \n")
            # print(f"連結： {link}")
            # print("-" * 40)
    result_string = "\n".join(result_list)
    return result_string

@line_handler.add(MessageEvent)
# @line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    working_status = True
    
    # print("event.message:", event.message)
    # print("event.message.type:",event.message.type)

    if event.message.type == "text":
        print("text")
        event_message_text = event.message.text

    elif event.message.type == "audio":
        print("audio")
        audio_message = line_bot_api.get_message_content(event.message.id)
        audio_data = audio_message.content

        # 語音辨識
        # client = speech.SpeechClient()
        # config = {
        #     "language_code": "en-US",
        # }
        # audio = {"content": audio_data}
        # response = client.recognize(config=config, audio=audio)
        
        # recognized_text = ""
        # for result in response.results:
        #     recognized_text += result.alternatives[0].transcript

        # message = recognized_text



    # elif event.message.type == "audio":
        # print("audio")
        # # message.append(TextSendMessage(text='聲音訊息'))
        # audio_content = line_bot_api.get_message_content(event.message.id)

        # # input_file = 'sound.m4a'
        # # with open(input_file, 'wb') as fd:
        # #     for chunk in audio_content.iter_content():
        # #         fd.write(chunk)
        # #         print("fd.write(chunk)")
        # with tempfile.NamedTemporaryFile(suffix=".m4a") as tf:
        #     for chuck in audio_content.iter_content():
        #         tf.write(chuck)
        #     # model = whisper.load_model("small")
        #     # transcript = model.transcribe(tf.name)
        #     # transcript = model.transcribe(tf.name, initial_prompt="今天的天氣、空氣都很好，適合出外郊遊。從陽台望出去，翠綠的平原盡收眼底，都市彷彿遠在天邊。什麼時候要出門呢？")

        #     #使用OpenAI whisper方法：
        #     # filename = tf + ".m4a"
        #     transcript = openai.Audio.transcribe("whisper-1", filename)
        #     print("transcript[\"text\"]")
        #     event_message_text = transcript["text"]
        #     print("event_message_text:", event_message_text)

        #     #將轉換的文字回傳給用戶
        #     message.append(TextSendMessage(text=event_message_text))
        #     line_bot_api.reply_message(event.reply_token, message)

    # elif event.message.type == "audio":
    #     print("audio")
    #     # message.append(TextSendMessage(text='聲音訊息'))
    #     audio_content = line_bot_api.get_message_content(event.message.id)
    #     print("audio_content:", audio_content)
    #     input_file = 'sound.m4a'
    #     with open(input_file, 'wb') as fd:
    #         for chunk in audio_content.iter_content():
    #             fd.write(chunk)
    #             print("fd.write(chunk)")
    #     os.chmod(input_file, 0o777)

        #進行語音轉文字處理
        r = sr.Recognizer()



        # AudioSegment.converter = './ffmpeg/bin/ffmpeg.exe'#輸入自己的ffmpeg.exe路徑
        # sound = AudioSegment.from_file_using_temporary_files(path)
        # path = os.path.splitext(path)[0]+'.wav'
        # sound.export(path, format="wav")
        # with sr.AudioFile(file) as source:
        #     audio = r.record(source)
        # event_message_text = r.recognize_google(audio, language='zh-Hant')#設定要以什麼文字轉換

        #測試：
        with sr.AudioFile(sr.AudioData(audio_data, sample_rate=16000, sample_width=2)) as source:
            audio_stream = r.open(audio_data=source.stream, sample_rate=16000, format="wav") # 將音訊文件轉換成可辨識的音訊物件
            event_message_text = r.recognize_google(audio_stream, show_all=False, language='zh-Hant')

        #使用OpenAI whisper方法：
        # transcript = openai.Audio.transcribe("whisper-1", input_file)
        # print("transcript[\"text\"]")
        # event_message_text = transcript["text"]
        # print("event_message_text:", event_message_text)



        #將轉換的文字回傳給用戶
        message.append(TextSendMessage(text=event_message_text))
        line_bot_api.reply_message(event.reply_token, message)

    else:
        return
        
    if working_status:
        print("working_status")
        print("event_message_text:", event_message_text)
        # chatgpt.add_msg(f"Human:{event_message_text}?\n")
        chatgpt.add_msg(f"Human:{event_message_text}，請使用繁體中文回答\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        # print("reply_msg:", reply_msg)
        # chatgpt.add_msg(f"AI:{reply_msg}\n")

        google_custom_search_api_key = os.getenv("google_custom_search_api_key")
        google_custom_search_cse_id = os.getenv("google_custom_search_cse_id")
        num_results = 3
        query = event_message_text
        google_custom_search_result = google_custom_search(google_custom_search_api_key, google_custom_search_cse_id, num_results, query)
        if len(google_custom_search_result) == 0:
            print("無搜尋結果")
        else:
            print("結果如下")
            print("result_list:", google_custom_search_result)
            # for i in google_custom_search_result:
            #     line_bot_api.reply_message(
            #         event.reply_token,
            #         TextSendMessage(text=i))
            reply_msg = reply_msg+"\n\n"+google_custom_search_result

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))

if __name__ == "__main__":
    app.run()