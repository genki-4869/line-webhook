from flask import Flask, request
import requests, json
import os
import requests

def get_ai_reply(user_text):
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "あなたは高校生の課題を管理するマネージャーとして、親切で賢く課題を管理します。もし、ユーザーから「〈科目〉〈期限〉〈内容〉」のように送られてきたら、それをわかりやすく、「https://1drv.ms/x/c/872cd97812562503/EeDbrmDmvF9Pmt49JFWxqzwBKDyzqA3K9XG-2yHdSZdhGw?e=VU5KfL」このファイルにまとめてください。ファイルに保存できたら、保存した内容を返答してください。また、「課題を確認する」と送られてきたら、送られた日にちから一週間以内の課題を表示してください。"},
            {"role": "user", "content": user_text}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    try:
        result = response.json()
        print("🧠 OpenRouter response:", json.dumps(result, indent=2))  # ← ここでログ確認
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ Error parsing OpenRouter response:", e)
        return "申し訳ありません、AIの応答に失敗しました。"





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
