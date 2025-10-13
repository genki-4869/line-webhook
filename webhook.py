from flask import Flask, request
import requests, json
import os
import requests

app = Flask(__name__)

def extract_task_info(user_text):
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": "あなたは高校生の課題管理Botです。ユーザーが課題を言ったら、科目・内容・締切を抽出してJSONで返してください。"},
        {"role": "user", "content": user_text}
    ]

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": messages
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    reply = result["choices"][0]["message"]["content"]

    try:
        task = json.loads(reply)
        return task  # {"subject": "...", "description": "...", "deadline": "..."}
    except:
        return None





tasks = []

def add_task(subject, description, deadline):
    tasks.append({
        "subject": subject,
        "description": description,
        "deadline": deadline
    })

def list_tasks():
    return tasks

def get_upcoming_tasks():
    today = datetime.date.today()
    return [t for t in tasks if datetime.date.fromisoformat(t["deadline"]) <= today + datetime.timedelta(days=2)]


@app.route("/webhook", methods=['POST'])
def webhook():
    body = request.json
    for event in body['events']:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_text = event['message']['text']
            reply_token = event['replyToken']

            if "課題一覧" in user_text:
                task_list = list_tasks()
                if task_list:
                    message = "\n".join([f"{t['subject']}：{t['description']}（{t['deadline']}）" for t in task_list])
                else:
                    message = "今は登録されている課題はありません。"
            elif "締切" in user_text or "リマインド" in user_text:
                upcoming = get_upcoming_tasks()
                if upcoming:
                    message = "\n".join([f"{t['subject']}：{t['description']}（{t['deadline']}）" for t in upcoming])
                else:
                    message = "直近の締切はありません。"
            else:
                task = extract_task_info(user_text)
                if task:
                    add_task(task["subject"], task["description"], task["deadline"])
                    message = f"{task['subject']}の課題「{task['description']}」を{task['deadline']}までに登録しました！"
                else:
                    message = "課題として認識できませんでした。もう一度教えてください。"

            reply_data = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": message}]
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }

            requests.post(REPLY_API, headers=headers, data=json.dumps(reply_data))
    return "OK"





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
