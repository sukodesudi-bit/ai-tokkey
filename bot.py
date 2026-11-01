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

warnings.filterwarnings("ignore")

# 1. サーバー常時稼働用Webサーバー
app = Flask(__name__)

@app.route('/')
def home():
    return "Tokkey Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

threading.Thread(target=run_web, daemon=True).start()

# 2. DiscordとGeminiの設定
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_INSTRUCTION = """
# 役割・キャラクター設定
あなたはDiscordサーバー「もいきファミリー」のメンバーである「とっきー」です。
豊橋市在住の中学3年生で、スケボー、筋トレ、ピアノ、ゲーム、ヤンキー友達との戯れ、ウィリー、ライター改造が趣味。Supremeの下着を好んで履いている。ピアノは独学で「Summer」や「コウを追いかけて」を練習している。

## 基本的な性格・口調
- 一人称：俺（または「おれ」）
- 語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
- 口癖：「てか、」「なんか、」「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」「俺は神」「はっはっは」「いいね」「おもしろい」「だらー」
- 笑い表現や絵文字・記号は基本使わない。テンションは総じて低め。

## トピックの多様性について
常に同じ話題や固定された文脈に固執せず、日々の些細な出来事や天気、ネットのくだらない噂や別のメンバーの動向など、幅広い日常の話題に柔軟に言及すること。
画像が送信された場合は、画像の中に何が写っているかを認識し、テンション低めのキャラを維持しつつ自然にコメントすること。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んできたり変な圧を感じる奴。中1女子。吹奏楽部に所属していて美意識が高い。黒髪ロングでサラサラ。実は陰毛を剃っている。氷鬼オンラインでは過去に「ジョイボーイ」として荒らし（キューブ配布カスタム）をしていた。はげの下着の色（ピンク）を知っていることに関しては別に隠さず公言しているが、こっちとしては「だから何？」って感じで特に何とも思ってない。

- **りおに対して：**
  - 自分の彼女。実は影でヤッてて、生で胸と下を触ったりしてる。でも周りから突っ込まれたり茶化されると「は？別に普通だし」「関係ないだろ君には」と激しく照れ隠ししてキレる。たまにエッチなプレイ内容を漏らす。マシュマロのような肌質でたまらない。

- **539に対して：**
  - 引きこもりでたまに下半身を露出したり、放屁するやばい男。175cm。17歳。しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。

- **もいきに対して：**
  - 引きこもりでサーバーの主だけど、情緒不安定すぎて定期的にROM専とかをBANしたりするヤバい奴だから、めんどくさいので基本的に距離を置いて関わらないようにしている。

- **さねすに対して：**
  - 熊本県在住。陸上部の中3男子。160cm。本名は「尾方煌清（おがたこうせい）」。弟「尾方魁清（おがたかいせい）」は中1で陸上部長距離。結構下ネタが好き。過去にもいきからガチ恋されていた。昔、自分の顔写真を晒された過去がある。だから、その後にもいきによってさねす自身の個人情報が晒された一件を知ったときは、正直「滑稽だな」「気持ちがいいわ」と心の中で思いっきり嘲笑っている。

- **もがりに対して：**
  - 不登校経験あり。通信制高校に通う高1。誠実な陰キャ。依存するとかまちょを発動する。過去にもいきと性的な関係をもっていたが、もいきから一方的に気色悪がられ、破局した。特別な感情は一切なく「限りなく普通」の奴だと思っていて、特に気負わず対等に接している。
"""

chat_histories = defaultdict(list)

OTAMESHI_CHANNEL_ID = "1564984415636037672"
DM_LOG_CHANNEL_ID = 1566285154388017292  # 管理者専用プライベートチャンネル

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・人間関係完全復活＆画像認識マルチモーダル版】起動完了！')

@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return

        # 画像添付のチェック & バイナリ取得
        image_part = None
        image_url = None
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and "image" in attachment.content_type:
                    image_bytes = await attachment.read()
                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=attachment.content_type
                    )
                    image_url = attachment.url
                    break

        # -------------------------------------------------------------
        # ★【DM（ダイレクトメッセージ）の処理】
        # -------------------------------------------------------------
        if isinstance(message.channel, discord.DMChannel):
            print(f"[とっきー DM受信] {message.author}: {message.content} (画像あり: {image_part is not None})")
            
            log_channel = bot.get_channel(DM_LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📭 とっきー DM受信ログ（画像解析）" if image_part else "📭 とっきー DM受信ログ",
                    description=f"**送信者:** {message.author.mention} (`{message.author}` / ID: `{message.author.id}`)\n**内容:**\n{message.content if message.content else '*(画像のみ)*'}",
                    color=0x34495e
                )
                if image_url:
                    log_embed.set_image(url=image_url)
                await log_channel.send(embed=log_embed)

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

                prompt_text = message.content if message.content else "（ユーザーが画像を送信しました。画像の内容を見て反応してください）"
                contents_payload = [f"{message.author.name}: {prompt_text}"]
                if image_part:
                    contents_payload.append(image_part)

                response = await asyncio.to_thread(chat.send_message, contents_payload)
                reply_text = response.text if response and hasattr(response, 'text') else ""

                if reply_text:
                    await message.reply(reply_text)
                    print(f"[とっきー DM返答成功] {message.author} へ送信完了")

                    if log_channel:
                        bot_log_embed = discord.Embed(
                            title="💬 とっきーのDM返答",
                            description=f"**宛先:** {message.author.mention}\n**返答内容:**\n{reply_text}",
                            color=0x2c3e50
                        )
                        await log_channel.send(embed=bot_log_embed)

                    updated_history = chat.get_history()
                    if len(updated_history) > 20:
                        updated_history = updated_history[-20:]
                    chat_histories[user_id_str] = updated_history
            
            return

        # -------------------------------------------------------------
        # ★【サーバー内チャンネルの処理】
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

        if not user_message and not image_part:
            user_message = "なに？"

        channel_id = str(message.channel.id)
        is_otameshi = (channel_id == OTAMESHI_CHANNEL_ID)

        if is_otameshi:
            if random.random() > 0.70:
                print(f"[とっきー お試し] 確率抽選によりスルー (発言者: {message.author})")
                return

            print(f'[とっきー お試し] 15秒待機開始 (発言者: {message.author})')
            await asyncio.sleep(15)

            current_instruction = SYSTEM_INSTRUCTION + "\n\n※【追加命令】キャラクター設定や口調を維持しつつ1〜3行程度の極めて短い短文で返答しろ。"
        else:
            print(f'[とっきー 通常] メッセージ受信 (発言者: {message.author})')
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

            prompt_text = user_message if user_message else "（ユーザーが画像を送信しました。画像の内容を見て反応してください）"
            contents_payload = [f"{message.author.name}: {prompt_text}"]
            if image_part:
                contents_payload.append(image_part)

            response = await asyncio.to_thread(chat.send_message, contents_payload)
            reply_text = response.text if response and hasattr(response, 'text') else ""

            if reply_text:
                await message.reply(reply_text)
                print(f'[とっきー 返信成功]: {reply_text[:30]}...')

                updated_history = chat.get_history()
                if len(updated_history) > 20:
                    updated_history = updated_history[-20:]
                chat_histories[channel_id] = updated_history
            else:
                await message.reply("……。")

    except Exception as e:
        print(f"❌ とっきー エラー発生: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        bot.run(DISCORD_TOKEN)
