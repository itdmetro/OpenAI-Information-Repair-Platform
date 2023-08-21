from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT
#import speech_recognition及pydub套件
import speech_recognition as sr
# from pydub import AudioSegment
from threading import Thread
import openai
import whisper
import tempfile
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

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def chatgpt_get_response():
    reply_msg = chatgpt.get_response().replace("AI:", "", 1)
    return reply_msg

def google_custom_search(query):
# def google_custom_search(api_key, cse_id, num_results, query):
    google_custom_search_api_key = os.getenv("google_custom_search_api_key")
    google_custom_search_cse_id = os.getenv("google_custom_search_cse_id")
    num_results = 3

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

    if event.message.type == "text":
        print("text")
        event_message_text = event.message.text

    elif event.message.type == "audio":
        print("audio")
        audio_message = line_bot_api.get_message_content(event.message.id)
        audio_data = audio_message.content

        #進行語音轉文字處理
        # r = sr.Recognizer()

        # AudioSegment.converter = './ffmpeg/bin/ffmpeg.exe'#輸入自己的ffmpeg.exe路徑
        # sound = AudioSegment.from_file_using_temporary_files(path)
        # path = os.path.splitext(path)[0]+'.wav'
        # sound.export(path, format="wav")
        # with sr.AudioFile(file) as source:
        #     audio = r.record(source)
        # event_message_text = r.recognize_google(audio, language='zh-Hant')#設定要以什麼文字轉換

        with tempfile.NamedTemporaryFile("w+b", suffix=".m4a") as fp:
            # print("fp:", type(fp))
            print("fp:", fp) #<class 'tempfile._TemporaryFileWrapper'>
            # print("fp.name:", type(fp.name))
            print("fp.name:", fp.name) #<class 'str'>
            fp_name = fp.name
            # print("fp_name:", fp_name)
            for chuck in audio_message.iter_content():
                fp.write(chuck)
            with open(fp_name, "rb") as tf:
                #使用OpenAI whisper方法：
                transcript = openai.Audio.transcribe("whisper-1", tf)
                # transcript = openai.Audio.transcribe("whisper-1", fp.name)
                print("transcript[\"text\"]")
                event_message_text = transcript["text"]
                print("event_message_text語音轉文字:", event_message_text)

    else:
        return
        
    if working_status:
        print("working_status")
        print("event_message_text收到文字:", event_message_text)
        # chatgpt.add_msg(f"Human:{event_message_text}?\n")
        chatgpt.add_msg(f"Human:{event_message_text}，請使用繁體中文回答\n")
        
        # google_custom_search_api_key = os.getenv("google_custom_search_api_key")
        # google_custom_search_cse_id = os.getenv("google_custom_search_cse_id")
        # num_results = 3
        query = event_message_text
        
        # reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        reply_msg = ThreadWithReturnValue(target=chatgpt_get_response)

        # google_custom_search_result = google_custom_search(google_custom_search_api_key, google_custom_search_cse_id, num_results, query)
        google_custom_search_result = ThreadWithReturnValue(target=google_custom_search, args=(query,))

        reply_msg.start()
        google_custom_search_result.start()
        reply_msg = reply_msg.join()        
        google_custom_search_result = google_custom_search_result.join()

        # chatgpt.add_msg(f"AI:{reply_msg}\n")
        print("reply_msg:", reply_msg)

        print("google_custom_search_result:", google_custom_search_result)
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