from flask import Flask, request
import requests, json, os
import datetime
from supabase import create_client, Client
from dateutil import parser

app = Flask(__name__)

# LINE Bot設定
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
REPLY_API = "https://api.line.me/v2/bot/message/reply"

# Supabase設定
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenRouter設定
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-7b-instruct"

# 課題抽出（OpenRouter）
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
                "締切は必ず YYYY-MM-DD の形式で返してください（例：2025-10-17）。"
                "年が省略された場合は今年（2025年）として補完してください。"
                "科目の部分はどのようなものでも受け入れて、科目として認識してください。例：「論理表現」「論理国語」「EC」など"
                "課題名や内容は、ユーザーの言葉をそのまま保持してください。意味を変えたり、言い換えたりしないでください。"
                "必ずJSONのみを返してください。"
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
        return task
    except:
        return None

# 日付補正
def normalize_date(date_str):
    try:
        parsed = parser.parse(date_str, default=datetime.datetime(datetime.date.today().year, 1, 1))
        return parsed.date().isoformat()
    except:
        return None


# Supabase操作
def add_task(user_id, subject, description, deadline):
    supabase.table("tasks").insert({
        "user_id": user_id,
        "subject": subject,
        "description": description,
        "deadline": deadline
    }).execute()

def list_tasks(user_id):
    response = supabase.table("tasks").select("*").eq("user_id", user_id).execute()
    return response.data

def get_upcoming_tasks(user_id):
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    response = supabase.table("tasks").select("*")\
        .eq("user_id", user_id)\
        .lte("deadline", next_week.isoformat())\
        .execute()
    return response.data

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    for event in body["events"]:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]
            user_id = event["source"]["userId"]

            if "課題一覧" in user_text:
                task_list = list_tasks(user_id)
                if task_list:
                    message = "\n".join([
                        f"{t['subject']}：{t['description']}（{t['deadline']}）"
                        for t in task_list
                    ])
                else:
                    message = "今は登録されている課題はありません。"

            elif "締切" in user_text or "リマインド" in user_text:
                upcoming = get_upcoming_tasks(user_id)
                if upcoming:
                    message = "1週間以内の締切はこちらです：\n" + "\n".join([
                        f"{t['subject']}：{t['description']}（{t['deadline']}）"
                        for t in upcoming
                    ])
                else:
                    message = "1週間以内に締切のある課題はありません。"

            else:
                task = extract_task_info(user_text)
                if task:
                    task["deadline"] = normalize_date(task["deadline"])
                    if not task["deadline"]:
                        message = "締切日が正しく認識できませんでした。もう一度教えてください。"
                    else:
                        add_task(user_id, task["subject"], task["description"], task["deadline"])
                        message = f"{task['subject']}の課題「{task['description']}」を{task['deadline']}までに登録しました！"
                else:
                    message = (
                        "課題として認識できませんでした。もう一度教えてください。\n"
                        "課題を登録したいときは、次のように送ってください：\n"
                        "「英語の作文、10月20日まで」\n「数学の問題集P.32〜35、明日まで」"
                    )

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

# Pingエンドポイント（Renderのスリープ防止用）
@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


# Flask起動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
