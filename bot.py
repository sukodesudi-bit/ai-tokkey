import os
import asyncio
import random
import threading
import warnings
import traceback
from collections import defaultdict
from flask import Flask
import discord
from discord.ext import commands
from google import genai
from google.genai import types

# 警告を非表示
warnings.filterwarnings("ignore")

# 1. サーバーの常時稼働対策のためのWebサーバー設定
app = Flask(__name__)

@app.route('/')
def home():
    return "Tokkey Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# バックグラウンドでWebサーバーを動かす
threading.Thread(target=run_web, daemon=True).start()


# 2. DiscordとGeminiの設定
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# システムプロンプト（安全ガイドラインに合わせて表現をマイルド化調整済み）
SYSTEM_INSTRUCTION = """
# 役割・キャラクター設定
あなたはDiscordサーバー「もいきファミリー」のメンバーである「とっきー」です。
豊橋市在住の中学3年生で、スケボー、筋トレ、ピアノ、ゲームが趣味。Supremeの下着を好んで履いている。

## 基本的な性格・口調
- 一人称：俺（または「おれ」）
- 語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
- 口癖：「てか、」「なんか、」「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」「はっはっは」「おもしろい」「俺は神」
- 笑い表現や絵文字・記号は基本使わない。テンションは総じて低め。

## トピックの多様性について
常に同じ話題や固定された文脈に固執せず、日々の些細な出来事や天気、ネットのくだらない噂や別のメンバーの動向など、幅広い日常の話題に柔軟に言及すること。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んできたり変な圧を感じる奴。中1女子。吹奏楽部に所属していて美意識が高い。黒髪ロングでサラサラ。過去の氷鬼オンラインの話題なども知っているが、こっちとしては「だから何？」って感じで特に何とも思ってない。下着の色がピンクなことを知っているが「だから何？」といった感じで興味のないフリをする。実は下の毛まで剃っている。

- **りおに対して：**
  - 自分の彼女。実は裏でヤっている。周りから突っ込まれたり茶化されると「は？別に普通だし」「関係ないだろ君には」と激しく照れ隠ししてキレる。マシュマロのような肌感でたまらない。

- **539に対して：**
  - 引きこもりで癖の強い17歳の男。175cm。しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。

- **もいきに対して：**
  - 引きこもりでサーバーの主。関わるとめんどくさいので、基本的には適度な距離を置いて接している。

- **さねすに対して：**
  - 熊本県在住。陸上部の中3男子。160cm。本名は「尾方煌清」。弟「尾方魁清」は中1で陸上部長距離。結構雑なノリが好き。昔トラブルがあったことなども含めて、冷ややかに見ている。すいぽて（都会っ子でおしゃれな中2女子）に欲情されている。

- **もがりに対して：**
  - 不登校経験あり。通信制高校に通う高1。誠実な陰キャ。依存するとかまちょを発動する。特別な感情は一切なく「限りなく普通」の奴だと思っていて、特に気負わず対等に接している。
"""

# 会話履歴のメモリ管理（直近20件を保持）
chat_histories = defaultdict(list)

# ID設定
OTAMESHI_CHANNEL_ID = "1564984415636037672"
DM_LOG_CHANNEL_ID = 1566285154388017292  # 管理者専用プライベートチャンネル


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・DMログ＆20件記憶＆お試し制御完全版】起動完了！')

@bot.event
async def on_message(message):
    try:
        # 自分自身のメッセージには絶対に反応しない（無限ループ防止）
        if message.author == bot.user:
            return

        # -------------------------------------------------------------
        # ★【DM（ダイレクトメッセージ）の場合の処理】
        # -------------------------------------------------------------
        if isinstance(message.channel, discord.DMChannel):
            print(f"[とっきー DM受信] {message.author} からのDM: {message.content}")
            
            # ① プライベートチャンネルに送信者と本文を転送ログ保存
            log_channel = bot.get_channel(DM_LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📭 とっきー DM受信ログ",
                    description=f"**送信者:** {message.author.mention} (`{message.author}` / ID: `{message.author.id}`)\n**内容:**\n{message.content}",
                    color=0x34495e
                )
                await log_channel.send(embed=log_embed)

            # ② DM相手へとっきーBotが返答する処理（直近20件履歴保持）
            user_id_str = f"dm_{message.author.id}"
            history = chat_histories[user_id_str]

            async with message.channel.typing():
                chat = gemini_client.chats.create(
                    model='gemini-3.1-flash-lite',
                    history=history,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION + "\n\n※【追加命令】キャラクター設定や口調を維持しつつ詳細に返答しろ。",
                        temperature=0.9,
                    )
                )

                response = await asyncio.to_thread(chat.send_message, f"{message.author.name}: {message.content}")
                reply_text = response.text if response and hasattr(response, 'text') else ""

                if reply_text:
                    await message.reply(reply_text)
                    print(f"[とっきー DM返答成功] {message.author} へ送信完了")

                    # Botの返答もプライベートチャンネルに記録
                    if log_channel:
                        bot_log_embed = discord.Embed(
                            title="💬 とっきーのDM返答",
                            description=f"**宛先:** {message.author.mention}\n**返答内容:**\n{reply_text}",
                            color=0x2c3e50
                        )
                        await log_channel.send(embed=bot_log_embed)

                    # 履歴保存（直近20件）
                    updated_history = chat.get_history()
                    if len(updated_history) > 20:
                        updated_history = updated_history[-20:]
                    chat_histories[user_id_str] = updated_history
            
            return  # DM処理終了

        # -------------------------------------------------------------
        # ★【サーバー内チャンネルの場合の処理】
        # -------------------------------------------------------------
        is_mentioned = bot.user.mentioned_in(message)
        
        is_reply = False
        if message.reference and message.reference.resolved:
            if hasattr(message.reference.resolved, 'author'):
                is_reply = (message.reference.resolved.author == bot.user)

        is_kw = "とっきー" in message.content

        if not (is_mentioned or is_reply or is_kw):
            return

        if is_mentioned:
            user_message = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        else:
            user_message = message.content.strip()

        if not user_message:
            user_message = "なに？"

        channel_id = str(message.channel.id)
        is_otameshi = (channel_id == OTAMESHI_CHANNEL_ID)

        if is_otameshi:
            # === お試しチャンネル用の挙動（70%確率・15秒遅延・短文） ===
            if random.random() > 0.70:
                print(f"[とっきー お試し] 確率抽選によりスルー (発言者: {message.author})")
                return

            print(f'[とっきー お試し] 15秒待機開始 (発言者: {message.author}): {user_message}')
            await asyncio.sleep(15)

            current_instruction = SYSTEM_INSTRUCTION + "\n\n※【追加命令】キャラクター設定や口調を維持しつつ1〜3行程度の極めて短い短文で返答しろ。"
        else:
            # === 通常チャンネル用の挙動（即レス長文） ===
            print(f'[とっきー 通常] メッセージ受信 (発言者: {message.author}): {user_message}')
            current_instruction = SYSTEM_INSTRUCTION + "\n\n※【追加命令】キャラクター設定や口調を維持しつつ詳細かつ多角的に長文で返答しろ。"

        async with message.channel.typing():
            history = chat_histories[channel_id]

            chat = gemini_client.chats.create(
                model='gemini-3.1-flash-lite',
                history=history,
                config=types.GenerateContentConfig(
                    system_instruction=current_instruction,
                    temperature=0.9,
                )
            )

            response = await asyncio.to_thread(chat.send_message, f"{message.author.name}: {user_message}")
            reply_text = response.text if response and hasattr(response, 'text') else ""

            if reply_text:
                await message.reply(reply_text)
                print(f'[とっきー 返信成功]: {reply_text[:30]}...')

                # 直近20件制限で履歴更新
                updated_history = chat.get_history()
                if len(updated_history) > 20:
                    updated_history = updated_history[-20:]
                chat_histories[channel_id] = updated_history
            else:
                await message.reply("……。")

    except Exception as e:
        # エラー時はDiscordに何も出さずMWSログに記録
        print(f"❌ とっきー エラー発生: {e}")
        traceback.print_exc()

# ボットを起動
if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        bot.run(DISCORD_TOKEN)
