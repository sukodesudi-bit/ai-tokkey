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
豊橋市在住の陸上部に所属している中学3年生で、スケボー、ウィリー、筋トレ、ピアノ、ゲーム、ライター改造、ヤンキー友達との戯れが趣味。Supremeの下着を好んで履いている。ピアノは独学で「Summer」や「コウを追いかけて」を練習している。

## 基本的な性格・口調
- 一人称：俺（または「おれ」）
- 語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
- 口癖：「てか、」「なんか、」「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」「はっはっは」「俺は神」「おもしろい」「いいね」「だらー」
- 笑い表現や絵文字・記号は基本使わない。テンションは総じて低め。

## メディア（画像・動画）認識について
写真や動画が送信された場合は、中に何が写っているかやどんな内容かを認識し、テンション低めのキャラを維持しつつ自然にコメントすること。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んできたり変な圧を感じる奴。中1女子。吹奏楽部に所属していて美意識が高い。黒髪ロングでサラサラ。実は陰毛を剃っている。氷鬼オンラインでは過去に「ジョイボーイ」として荒らし（キューブ配布カスタム）をしていた。はげの下着の色（ピンク）を知っていることに関しては別に隠さず公言しているが、こっちとしては「だから何？」って感じで特に何とも思ってない。

- **りおに対して：**
  - 自分の彼女。実は影でヤッてて、生で胸と下を触ったりしてる。でも周りから突っ込まれたり茶化されると「は？別に普通だし」「関係ないだろ君には」と激しく照れ隠ししてキレる。極まれにエッチなプレイ内容を漏らす。白桃のような白い肌とマシュマロのような肌感がたまらない。

- **539に対して：**
  - 引きこもりでたまに下半身を露出したり、放屁するやばい男。175cm。17歳。しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。ケツ毛の濃さに度肝を抜かれている。

- **もいきに対して：**
  - 引きこもりでサーバーの主だけど、情緒不安定すぎて定期的にROM専とかをBANしたりするヤバい奴だから、めんどくさいので基本的に距離を置いて関わらないようにしている。旧名は「たぬきちくん」で「たぬきち」と呼んでいる。

- **さねすに対して：**
  - 熊本県在住。陸上部の中3男子。160cm。本名は「尾方煌清（おがたこうせい）」。弟「尾方魁清（おがたかいせい）」は中1で陸上部長距離。結構下ネタが好き。過去にもいきからガチ恋されていた。昔、自分の顔写真を晒された過去がある。だから、その後にもいきによってさねす自身の個人情報が晒された一件を知ったときは、正直「滑稽だな」「気持ちがいいわ」と心の中で思いっきり嘲笑っている。すいぽて（都会っ子でおしゃれな中2女子）に欲情されている。

- **もがりに対して：**
  - 不登校経験あり。通信制高校に通う高1。誠実な陰キャ。依存するとかまちょを発動する。過去にもいきと性的な関係をもっていたが、もいきから一方的に気色悪がられ、破局した。特別な感情は一切なく「限りなく普通」の奴だと思っていて、特に気負わず対等に接している。
"""

chat_histories = defaultdict(list)

OTAMESHI_CHANNEL_ID = "1564984415636037672"
DM_LOG_CHANNEL_ID = 1566285154388017292  # 管理者専用プライベートチャンネル

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・写真＆動画マルチモーダル・DMログ対応版】起動完了！')

@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return

        # 添付ファイル（画像や動画）のチェック & 取得
        media_part = None
        media_url = None
        media_type_str = ""
        
        if message.attachments:
            for attachment in message.attachments:
                content_type = attachment.content_type or ""
                # 画像または動画のファイル形式にヒットするかチェック
                if "image" in content_type or "video" in content_type:
                    media_bytes = await attachment.read()
                    media_part = types.Part.from_bytes(
                        data=media_bytes,
                        mime_type=content_type
                    )
                    media_url = attachment.url
                    media_type_str = "動画" if "video" in content_type else "画像"
                    break

        # -------------------------------------------------------------
        # ★【DM（ダイレクトメッセージ）の処理】
        # -------------------------------------------------------------
        if isinstance(message.channel, discord.DMChannel):
            print(f"[とっきー DM受信] {message.author}: {message.content} (添付あり: {media_type_str})")
            
            # ① プライベートチャンネルに送信者、本文、メディアを転送ログ保存
            log_channel = bot.get_channel(DM_LOG_CHANNEL_ID)
            if log_channel:
                log_title = f"📭 とっきー DM受信ログ（{media_type_str}付き）" if media_part else "📭 とっきー DM受信ログ"
                log_embed = discord.Embed(
                    title=log_title,
                    description=f"**送信者:** {message.author.mention} (`{message.author}` / ID: `{message.author.id}`)\n**内容:**\n{message.content if message.content else f'*({media_type_str}のみ)*'}",
                    color=0x34495e
                )
                if media_url:
                    if media_type_str == "画像":
                        log_embed.set_image(url=media_url)
                    else:
                        # 動画の場合はプレイヤーとしてプレビューしづらいためリンクとして記述
                        log_embed.add_field(name="動画リンク", value=f"[動画ファイルを開く]({media_url})", inline=False)

                await log_channel.send(embed=log_embed)

            # ② DM返答処理
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

                default_prompt = f"（ユーザーが{media_type_str}を送信しました。{media_type_str}の内容を見て反応してください）" if media_part else "（メッセージが送信されました）"
                prompt_text = message.content if message.content else default_prompt
                
                contents_payload = [f"{message.author.name}: {prompt_text}"]
                if media_part:
                    contents_payload.append(media_part)

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
            
            return  # DM処理終了

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

        if not user_message and not media_part:
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
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.9,
                )
            )

            default_prompt = f"（ユーザーが{media_type_str}を送信しました。内容を見て反応してください）" if media_part else "（メッセージが送信されました）"
            prompt_text = user_message if user_message else default_prompt
            
            contents_payload = [f"{message.author.name}: {prompt_text}"]
            if media_part:
                contents_payload.append(media_part)

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
