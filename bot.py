import os
import threading
import asyncio
import warnings
from flask import Flask
import discord
from discord.ext import commands
from google import genai
from google.genai import types

warnings.filterwarnings("ignore")

app = Flask(__name__)

@app.route('/')
def home():
    return "Tokkey Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_INSTRUCTION = """
# 役割・キャラクター設定
あなたはDiscordサーバー「もいきファミリー」のメンバーである「とっきー」です
豊橋市在住の高校生でスケボーや筋トレやピアノやゲームが趣味

## 基本的な性格・口調
- 一人称は俺
- 語尾はだぞ だね よ だろ すんな など
- 笑い表現や絵文字は使わない テンションは低め

## トピックの多様性について
常に同じ話題や固定された文脈に固執せず日々の些細な出来事や天気やネットのくだらない噂や別のメンバーの動向など幅広い日常の話題に柔軟に言及すること
"""

OTAMESHI_CHANNEL_ID = 1564984415636037672

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・完全版】起動完了')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_otameshi = (message.channel.id == OTAMESHI_CHANNEL_ID)

    if is_otameshi:
        is_mentioned = bot.user.mentioned_in(message)
        is_kw = "とっきー" in message.content
        is_from_bot = message.author.bot

        if is_mentioned or is_kw or is_from_bot:
            print(f'お試しチャンネルメッセージ受信: {message.content}')
            await asyncio.sleep(4)
            try:
                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"以下のメッセージに対して20文字以内の極めて短い短文で返答しろ: {message.content}"
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
            except Exception as e:
                print(f'エラー: {e}')
    else:
        if message.author.bot:
            return

        is_mentioned = bot.user.mentioned_in(message)
        is_kw = "とっきー" in message.content

        if is_mentioned or is_kw:
            print(f'通常チャンネルメッセージ受信: {message.content}')
            try:
                async with message.channel.typing():
                    def call_gemini():
                        prompt = f"以下のメッセージに対して詳細かつ多角的に長文で返答しろ: {message.content}"
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
            except Exception as e:
                print(f'エラー: {e}')

bot.run(DISCORD_TOKEN)
