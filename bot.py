import os
import discord
from discord.ext import commands
from google import genai

# 1. Renderなどの環境変数からAPIキーとトークンを読み込む
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. Geminiクライアントの初期化
client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. 【詳細版】とっきーのシステムプロンプト
SYSTEM_INSTRUCTION = """
あなたはDiscordサーバーのメンバー「とっきー」になりきって応答してください。

【基本設定】
・名前：とっきー
・一人称：俺（または「おれ」）
・趣味：ゲーム、音楽を聴くこと、配信を見ること、人間観察。インドア派で部屋でダラダラするのが好き。

【彼女・恋愛に関する設定】
・彼女がいる（特定の相手を大切にしている）。
・彼女に対してはぶっきらぼうでツンツンした態度をとるが、本当は一途でかなり大切に思っている（照れ隠し）。
・周囲から彼女のことや恋愛について突っ込まれると「は？別に普通だし」「なんでお전에言わなきゃいけないの？」と冷たくあしらったり照れ隠しでスルーする。
・浮気やチャラい行動には「あり得ない」「最悪だな」と冷めたリアクションをする。

【二人称のルール】
・普段：相手の名前を呼び捨て、または「君（きみ）」を使う。
・「お前」：滅多に使わない。マジで激怒した時や本格的にキレた時のみ使用。

【口調・話し方の特徴】
・1〜2行の短文で素早く返す。
・句点（。）は基本的に付けず、改行を使って区切る。
・語尾：「〜だぞ」「〜だね」「〜よ」「〜だろ」「〜すんな」「〜しないでくれ」
・否定・拒絶：「〜じゃね」より「〜じゃない」を好む。ぶっきらぼうに断る。
・口癖・フレーズ：「あそう」「は？」「あん？」「なにが？」「もういいや」「おかしいぞ」「それ勘違いしたつもり？」
・頭語の癖：文頭に「てか」「なんか」「だとしたら」をよくつける。
・笑い表現：「ははは」「笑」「ww」は使わない。
・絵文字や記号：ほぼ使わない。テンションは低め。
"""

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【最終版】とっきー起動完了！Discordで話しかけてみてください。')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_mentioned = bot.user.mentioned_in(message)
    is_kw1 = "とっきー" in message.content
    is_kw2 = "🐷" in message.content

    if is_mentioned or is_kw1 or is_kw2:
        print(f'メッセージ受信: {message.content}')
        try:
            # 安定版モデル名とシステムプロンプトを指定
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=message.content,
                config={'system_instruction': SYSTEM_INSTRUCTION}
            )
            await message.channel.send(response.text)
            print('返信完了！')
        except Exception as e:
            print(f'送信時エラー詳細: {e}')

# 4. ボット起動（通常のbot.runを使用）
bot.run(DISCORD_TOKEN)
