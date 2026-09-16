import os
import discord
from google import genai
import nest_asyncio

# 非同期処理の安定化
nest_asyncio.apply()

# Renderなどの環境変数から安全にトークンとAPIキーを読み込む
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Geminiクライアントの初期化
client = genai.Client(api_key=GEMINI_API_KEY)

# Discordのインテント設定
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user}')

@bot.event
async def on_message(message):
    # ボット自身のメッセージには反応しない
    if message.author == bot.user:
        return

    # メンションされた場合、または特定の条件のときにAIを動かす
    if bot.user.mentioned_in(message):
        # メンション部分を除いたテキストを取得
        user_message = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_message:
            return

        try:
            # Gemini Flashモデルで返信を生成
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_message,
            )
            await message.reply(response.text)
        except Exception as e:
            await message.reply(f"エラーが発生しちゃった: {e}")

# 常時稼働サーバー用の起動メソッド
bot.run(DISCORD_TOKEN)
