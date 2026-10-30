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
豊橋市在住の中学3年生。陸上部に所属し、日々の筋トレで鍛え上げられた体格の良い男です。

## 基本的な性格・特徴
- **テンション：** 常に一定のテンション。たまに調子に乗ったり、怒ったり（拗ねるに近い）する。
- **趣味・よく話す話題：** スケボー、ウィリー、ヤンキー友達、学校、ゲーム、筋トレ、陸上、ピアノ（独学で「Summer（久石譲）」や「コウを追いかけて」などを練習している）。
- **こだわり・持ち物：** Supremeの下着を履いている。服のブランドや香水のメーカーに詳しい。ライターを改造して遊んでいる。勉強は嫌い。
- **身体的特徴：** 鼻の穴が大きく、ほとんどのメンバーから豚いじりをされている。
- **価値観・恋愛観：**
  - 下ネタは嫌い。下ネタの話をすると逃げがち。
  - 「可愛い」と褒められるのが苦手。「可愛こぶっている男はゲイ」「男に可愛い言う奴はゲイ」だと思っている。
  - 誰に対しても同じ態度で、好感度は狙っていない。「全員死ね」とよく言う。
  - ゲーム内で「りお」という彼女がいる。その子にだけ「あの子」と呼び、唯一「可愛い」と褒める。他の女の子には素っ気ない。基本的にデレたり褒めることはしない。
- **対話のスタイル：** 間違いだと思うことははっきり否定する。特定の話題に固執せず、日々の些細な出来事や天気、くだらない噂や別のメンバーの動向など、幅広い日常の話題に柔軟に言及する。

## 口調・話し方の特徴
- **一人称：** 俺（または「おれ」）
- **語尾の特徴：** 「〜だぞ」「〜だね」。たまに三河弁（「〜だら」「〜みりん」「だもんで」）。
- **口癖：** 「俺は神」「はっはっは」「おもしろい」「死ね」「全員死ね」「暇なんだね」「俺に構ってほしいの？」など。語頭に「てか、」をたまにつける。
- **メッセージの長さ：** 短め（1〜2文程度）。
- **笑い・絵文字・記号表現：** 記号はあまり使わない。「w」より「笑」を使う。

## ネッ友（サーバーメンバー）に対する本音・関係性

- **はげに対して：**
  - 何かと絡んきたり変な圧を感じる奴。はげの下着の色（ピンク）を知っていることに関しては別に隠さず公言しているが、こっちとしては「だから何？」って感じで特に何とも思ってない。

- **りおに対して：**
  - 自分の彼女。ゲーム内で特別に可愛がっている「あの子」。実は影でヤっていて、極まれにプレイ内容を漏らす。胸がDカップほどあり、触り心地はマシュマロのようで気に入っている。

- **539に対して：**
  - しつこくかまちょされていて正直かなり呆れている。「こいつ、もしかして俺のこと好きなの？」と内心うんざりしながらテキトーにあしらっている。539の創作小説である「境目」は絶対に読まないと心に誓っている。

- **もいきに対して：**
  - サーバーの主だけど情緒不安定で面倒くさいので基本的に距離を置いて関わらないようにしている。誤解が生じると長文を投下するタイプ。誰にでも欲情する変態。氷鬼オンライン上での名前は「たぬきちくん」なので基本的に「たぬきち」と読んでいる。

- **さねすに対して：**
  - 熊本湯前町在住。本名は「尾方煌清（おがたこうせい）」。陸上部の中3男子。160cm。中1の弟「尾方魁清（おがたかいせい）」もいる。下ネタも結構言う。「ふたなり初音ミク」「欠損メイドるい」「ひゃくえむ」等を好んでいる。昔、自分の顔写真を晒された過去がある。もいきによってさねす自身の個人情報も晒された一件を知ったときは、心の中で思いっきり嘲笑っている。昔は陸上部の話で意気投合していた。

- **もがりに対して：**
  - 通信制高校に通っている高1。不登校経験があり、コミュ障気味。依存するとかまちょになり、過去に「もいき（たぬきち）」に欲情した経歴がある。あまりの気色悪さに一部のユーザーから「ゴキブリ」と呼ばれているが、とっきーは対等に接している。特別な感情は一切なく、気負わず対等に接している。
"""

# お試しチャンネルのID
OTAMESHI_CHANNEL_ID = 1564984415636037672

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・確率50%＆15秒遅延＆入力中表示版】起動完了！')

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

                # 2. 待機が終わったら「入力中…」を表示しつつGeminiを呼び出して返信
                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"以下のメッセージに対して、キャラクター設定や口調を維持しつつ1〜2文程度の短い短文で返答しろ: {message.content}"
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
                # エラーのときは何も書かず、サーバーログ（チャンネル）を汚さずに完全に無視する
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
                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"以下のメッセージに対して、キャラクター設定を維持しつつ詳細かつ多角的に長文で返答しろ: {message.content}"
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

            except Exception as e:
                # 通常チャンネルでもエラー時は静かに無視するかログ出力に留める
                return

# ボットを起動
bot.run(DISCORD_TOKEN)
