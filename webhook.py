from flask import Flask, request
import requests, json


import openai
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_ai_reply(user_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはLINE Botとして、親切で賢く、簡潔にユーザーの質問に答えます。"},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content


app = Flask(__name__)


ACCESS_TOKEN = '1eWjiMP/MusTUmfEnR9mo48kJNHHJLmz+C0c8v+74ogqym1YGRryOLQWcASizMORchMZLqw1PnunoZr8CnfDzgLeF2wUF46o3Cx7wFKt6GXftfYzDwbcxlh9RXYvZr9sfHOI2EzCUzHcw9BiSQf39wdB04t89/1O/w1cDnyilFU='
REPLY_API = 'https://api.line.me/v2/bot/message/reply'


@app.route("/webhook", methods=['POST'])
def webhook():
    body = request.json
    for event in body['events']:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            reply_token = event['replyToken']
            user_text = event['message']['text']

            ai_text = get_ai_reply(user_text)

            reply_data = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "text",
                        "text": ai_text
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }
            requests.post(REPLY_API, headers=headers, data=json.dumps(reply_data))
    return "OK"


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
