# 以下はPythonで同様の機能を実現するための基本的なコード例です。

from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
import base64
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage


# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# 環境変数から必要な設定を取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ZOOM_VERIFICATION_TOKEN = os.getenv("ZOOM_VERIFICATION_TOKEN")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_BOT_JID = os.getenv("ZOOM_BOT_JID")


@app.route('/gpt_chat', methods=['POST'])
def gpt_chat():
    # Zoomからの認証チェック
    if request.headers.get('Authorization') == ZOOM_VERIFICATION_TOKEN:
        user_input = request.json['payload']['cmd']
        
        # OpenAI API にリクエストを送信
        openai_response = get_openai_response(user_input)

        if openai_response:
            chatbot_token = get_chatbot_token()
            send_chat(request.json, chatbot_token, openai_response)
            return jsonify(success=True)
        else:
            return jsonify(error="No response from OpenAI"), 500
    else:
        return jsonify(error="Authorization failed"), 403


def get_openai_response(text):
    # headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
    # data = {
    #     'prompt': text,
    #     'max_tokens': 150
    # }
    # response = requests.post('https://api.openai.com/v1/engines/text-davinci-003/completions', json=data, headers=headers)
    # if response.status_code == 200:
    #     return response.json()['choices'][0]['text'].strip()
    # else:
    #     return None
# def get_openai_response_with_langchain(text):
    # ChatOpenAIのインスタンスを作成
    chat_model = ChatOpenAI(api_key=OPENAI_API_KEY)

    # リクエストを送信し、応答を取得
    text = [HumanMessage(content=text)]
    response = chat_model(text)
    # print(response.content)

    # 応答が正常に取得できた場合はテキストを返す
    if response:
        return response.content
    else:
        return None


def get_chatbot_token():
    combined_credentials = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(combined_credentials.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    response = requests.post('https://zoom.us/oauth/token?grant_type=client_credentials', headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        if 'access_token' in json_response:
            return json_response['access_token']
        else:
            print(f"Error: 'access_token' not found in response. Response content: {json_response}")
            return None
    else:
        print(f"Error making request to Zoom API. Status code: {response.status_code}, Response content: {response.text}")
        return None



def send_chat(payload, chatbot_token, message):
    headers = {
        'Authorization': f'Bearer {chatbot_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'robot_jid': ZOOM_BOT_JID,
        'to_jid': payload['payload']['toJid'],
        'account_id': payload['payload']['accountId'],
        'content': {
            'head': {'text': 'Response'},
            'body': [{'type': 'message', 'text': message}]
        }
    }
    requests.post('https://api.zoom.us/v2/im/chat/messages', json=data, headers=headers)


if __name__ == '__main__':
    app.run(port=os.getenv("PORT", 4000))
