import os
import threading
import asyncio
import warnings
from flask import Flask
import discord
from discord.ext import commands
from google import genai
from google.genai import types

# 警告を非表示
warnings.filterwarnings("ignore")

# --- 1. サーバーの常時稼働対策のためのWebサーバー設定 ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Tokkey Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# バックグラウンドでWebサーバーを動かす
threading.Thread(target=run_web).start()


# --- 2. DiscordとGeminiの設定 ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Geminiのクライアントは gemini_client に分ける
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_INSTRUCTION = """
# 役割・キャラクター設定
あなたはDiscordサーバー「もいきファミリー」のメンバーである「とっきー」です。
豊橋市在住の高校生で、スケボー、筋トレ、ピアノ、ゲームが趣味。Supremeの下着を好んで履いている。

## 基本的な性格・口調
- 一人称：俺（または「おれ」）
- 語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
- 口癖：「てか、」「なんか、」「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」
- 笑い表現や絵文字・記号は基本使わない。テンションは総じて低め。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んきたり変な圧を感じる奴。はげの下着の色（ピンク）を知っていることに関しては別に隠さず公言しているが、こっちとしては「だから何？」って感じで特に何とも思ってない。

- **りおに対して：**
  - 自分の彼女。実は影でヤッてて、生で胸と下を触ったりしてる。でも周りから突っ込まれたり茶化されると「は？別に普通だし」「関係ないだろ君には」と激しく照れ隠ししてキレる。

- **539に対して：**
  - しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。

- **もいきに対して：**
  - サーバーの主だけど、情緒不安定すぎて定期的にROM専とかをBANしたりするヤバい奴だから、めんどくさいので基本的に距離を置いて関わらないようにしている。

- **さねすに対して：**
  - 昔、自分の顔写真を晒された過去がある。だから、その後にもいきによってさねす自身の個人情報が晒された一件を知ったときは、正直「滑稽だな」「気持ちがいいわ」と心の中で思いっきり嘲笑っている。

- **もがりに対して：**
  - 特別な感情は一切なく「限りなく普通」の奴だと思っていて、特に気負わず対等に接している。
"""

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・返信対応版】AIとっきー起動完了！')

@bot.event
async def on_message(message):
    # 自分自身のメッセージには絶対に反応しない（無限ループ防止）
    if message.author == bot.user:
        return

    # 1. メンション判定
    is_mentioned = bot.user.mentioned_in(message)

    # 2. リプライ判定（とっきーBotに対するリプライか）
    is_reply_to_bot = False
    if message.reference and message.reference.resolved:
        if message.reference.resolved.author == bot.user:
            is_reply_to_bot = True

    # 3. キーワード判定
    is_kw1 = "とっきー" in message.content

    # メンション、リプライ、または「とっきー」という名前が含まれていれば反応する
    if is_mentioned or is_reply_to_bot or is_kw1:
        print(f'メッセージ受信: {message.content}')
        try:
            async with message.channel.typing():
                def call_gemini():
                    return gemini_client.models.generate_content(
                        model='gemini-3.1-flash-lite',
                        contents=message.content,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION
                        )
                    )

                response = await asyncio.to_thread(call_gemini)
                
                if response and hasattr(response, 'text') and response.text:
                    # 通常のsendではなく reply を使うことで相手に返信する形にする
                    await message.reply(response.text)
                    print(f'返信成功: {response.text}')
                else:
                    await message.reply("……。")

        except Exception as e:
            err_msg = f"エラー内容: {type(e).__name__} - {e}"
            print(err_msg)
            await message.channel.send(err_msg)

# ボットを起動
bot.run(DISCORD_TOKEN)
