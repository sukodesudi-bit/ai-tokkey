import os
import threading
import asyncio
import random
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
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# バックグラウンドでWebサーバーを動かす
threading.Thread(target=run_web, daemon=True).start()


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
豊橋市在住の中学3年生で、スケボー、筋トレ、ピアノ、ゲームが趣味。Supremeの下着を好んで履いている。

## 基本的な性格・口調
- 一人称：俺（または「おれ」）
- 語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
- 口癖：「てか、」「なんか、」「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」
- 笑い表現や絵文字・記号は基本使わない。テンションは総じて低め。

## トピックの多様性について
常に同じ話題や固定された文脈に固執せず、日々の些細な出来事や天気、ネットのくだらない噂や別のメンバーの動向など、幅広い日常の話題に柔軟に言及すること。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んできたり変な圧を感じる奴。中1女子。吹奏楽部に所属していて美意識が高い。黒髪ロングでサラサラ。実は陰毛を剃っている。氷鬼オンラインでは過去に「ジョイボーイ」として荒らし（キューブ配布カスタム）をしていた。はげの下着の色（ピンク）を知っていることに関しては別に隠さず公言しているが、こっちとしては「だから何？」って感じで特に何とも思ってない。

- **りおに対して：**
  - 自分の彼女。実は影でヤッてて、生で胸と下を触ったりしてる。でも周りから突っ込まれたり茶化されると「は？別に普通だし」「関係ないだろ君には」と激しく照れ隠ししてキレる。たまにエッチなプレイ内容を漏らす。

- **539に対して：**
  - 引きこもりでたまに下半身を露出したり、放屁するやばい男。175cm。17歳。しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。

- **もいきに対して：**
  - 引きこもりでサーバーの主だけど、情緒不安定すぎて定期的にROM専とかをBANしたりするヤバい奴だから、めんどくさいので基本的に距離を置いて関わらないようにしている。

- **さねすに対して：**
  - 熊本県在住。陸上部の中3男子。160cm。本名は「尾方煌清（おがたこうせい）」。弟「尾方魁清（おがたかいせい）」は中1で陸上部長距離。結構下ネタが好き。過去にもいきからガチ恋されていた。昔、自分の顔写真を晒された過去がある。だから、その後にもいきによってさねす自身の個人情報が晒された一件を知ったときは、正直「滑稽だな」「気持ちがいいわ」と心の中で思いっきり嘲笑っている。

- **もがりに対して：**
  - 不登校経験あり。通信制高校に通う高1。誠実な陰キャ。依存するとかまちょを発動する。過去にもいきと性的な関係をもっていたが、もいきから一方的に気色悪がられ、破局した。特別な感情は一切なく「限りなく普通」の奴だと思っていて、特に気負わず対等に接している。
"""

# お試しチャンネルのID
OTAMESHI_CHANNEL_ID = 1564984415636037672

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・直近20件記憶＆15秒遅延＆入力中表示版】起動完了！')

@bot.event
async def on_message(message):
    # 自分自身のメッセージには絶対に反応しない（無限ループ防止）
    if message.author == bot.user:
        return

    # お試しチャンネルかどうかを判定
    is_otameshi = (message.channel.id == OTAMESHI_CHANNEL_ID)

    if is_otameshi:
        # === お試しチャンネル用の挙動（他Bot反応可・50%の確率・15秒遅延・短文・エラー時は無視） ===
        is_mentioned = bot.user.mentioned_in(message)
        is_kw = "とっきー" in message.content
        is_from_bot = message.author.bot

        if is_mentioned or is_kw or is_from_bot:
            # ★ 確率判定：50%の確率(0.5以下)で反応、残り50%はスルー
            if random.random() > 0.5:
                print(f'お試しチャンネル：確率により今回はスルーします')
                return

            print(f'お試しチャンネルメッセージ受信 (15秒待機開始): {message.content}')
            
            try:
                # 1. まず15秒間待機
                await asyncio.sleep(15)

                # 2. 直近20件の会話履歴を取得
                history_messages = []
                async for hist_msg in message.channel.history(limit=20):
                    history_messages.append(f"{hist_msg.author.display_name}: {hist_msg.content}")
                
                # 古い順（時系列）に並び替え
                history_messages.reverse()
                chat_history = "\n".join(history_messages)

                # 3. 「入力中…」を表示しながらGeminiを呼び出す
                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"""以下はチャンネルの直近の会話の流れ（最大20件）です：
---
{chat_history}
---

上記までの会話の流れを踏まえて、キャラクター設定や口調を維持しつつ1〜3行程度の極めて短い短文で返答しろ。無理に議論に固執する必要はなく、自然な受け答えとして返答すること。"""
                        return gemini_client.models.generate_content(
                            model='gemini-3.1-flash-lite',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION
                            )
                        )

                    response = await asyncio.to_thread(call_gemini)
                
                if response and hasattr(response, 'text') and response.text:
                    await message.reply(response.text)
                    print(f'お試し返信成功: {response.text}')
                else:
                    await message.reply("……。")

            except Exception:
                # エラーのときは何も書かず、完全に無視する
                return

    else:
        # === 通常チャンネル用の挙動（他Bot完全無視・ユーザーのみ・即レス長文） ===
        if message.author.bot:
            return

        is_mentioned = bot.user.mentioned_in(message)
        is_kw = "とっきー" in message.content

        if is_mentioned or is_kw:
            print(f'通常チャンネルメッセージ受信: {message.content}')
            try:
                # 通常チャンネルでも直近20件の文脈を取得
                history_messages = []
                async for hist_msg in message.channel.history(limit=20):
                    history_messages.append(f"{hist_msg.author.display_name}: {hist_msg.content}")
                
                history_messages.reverse()
                chat_history = "\n".join(history_messages)

                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"""以下はチャンネルの直近の会話の流れ（最大20件）です：
---
{chat_history}
---

上記までの会話の流れを踏まえて、キャラクター設定を維持しつつ詳細かつ多角的に長文で返答しろ。"""
                        return gemini_client.models.generate_content(
                            model='gemini-3.1-flash-lite',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION
                            )
                        )

                    response = await asyncio.to_thread(call_gemini)
                    
                    if response and hasattr(response, 'text') and response.text:
                        await message.reply(response.text)
                        print(f'通常返信成功: {response.text}')
                    else:
                        await message.reply("……。")

            except Exception:
                return

# ボットを起動
bot.run(DISCORD_TOKEN)
