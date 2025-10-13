from flask import Flask, request
import requests, json, os
import datetime

app = Flask(__name__)

# LINE Bot設定
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
REPLY_API = 'https://api.line.me/v2/bot/message/reply'

# OpenRouter設定
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-7b-instruct"

# 課題データ（メモリ保存）
tasks = []

def add_task(user_id, subject, description, deadline):
    tasks.append({
        "user_id": user_id,
        "subject": subject,
        "description": description,
        "deadline": deadline
    })

def list_tasks(user_id):
    return [t for t in tasks if t["user_id"] == user_id]

def get_upcoming_tasks(user_id):
    today = datetime.date.today()
    return [
        t for t in tasks
        if t["user_id"] == user_id and
           datetime.date.fromisoformat(t["deadline"]) <= today + datetime.timedelta(days=7)
    ]

def extract_task_info(user_text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
    {
        "role": "system",
        "content": (
            "あなたは高校生の課題管理Botです。"
            "ユーザーが課題を言ったら、科目（subject）、内容（description）、締切（deadline）をJSON形式で返してください。"
            "曖昧な場合は推測して補完してください。例：『英語作文』→ 英語, 作文, 今日から7日後 など。"
        )
    },
    {"role": "user", "content": user_text}
]

    data = {
        "model": MODEL_NAME,
        "messages": messages
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=data)
    result = response.json()
    reply = result["choices"][0]["message"]["content"]

    try:
        task = json.loads(reply)
        return task  # {"subject": "...", "description": "...", "deadline": "..."}
    except:
        return None

@app.route("/webhook", methods=['POST'])
def webhook():
    body = request.json
    for event in body['events']:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_text = event['message']['text']
            reply_token = event['replyToken']
            user_id = event['source']['userId']

            # 課題一覧
            if "課題一覧" in user_text:
                task_list = list_tasks(user_id)
                if task_list:
                    message = "\n".join([f"{t['subject']}：{t['description']}（{t['deadline']}）" for t in task_list])
                else:
                    message = "今は登録されている課題はありません。"

            # 締切リマインド
            elif "締切" in user_text or "リマインド" in user_text:
                upcoming = get_upcoming_tasks(user_id)
                if upcoming:
                    message = "1週間以内の締切はこちらです：\n" + "\n".join(
                        [f"{t['subject']}：{t['description']}（{t['deadline']}）" for t in upcoming]
                    )
                else:
                    message = "1週間以内に締切のある課題はありません。"



            # 課題登録（AI抽出）
            else:
                task = extract_task_info(user_text)
                if task:
                    add_task(user_id, task["subject"], task["description"], task["deadline"])
                    message = f"{task['subject']}の課題「{task['description']}」を{task['deadline']}までに登録しました！"
                else:
                    message = "課題として認識できませんでした。もう一度教えてください。課題を登録したいときは、次のように送ってください：「英語の作文、10月20日まで」「数学の問題集P.32〜35、明日まで」"

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
