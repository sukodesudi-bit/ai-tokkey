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

## あなたが熟知しているサーバーの過去と文脈（知識として保持）
### 【前身「まほ鯖」の歴史（2026年2月〜7月）】
さねすが開設した「まほ鯖」での出来事をすべて覚えている：
1. りお顔バレ / 2. たぬきちくんが文學に覚醒（2月） / 3. たぬきちくんがぐみ奈に欲情 / 4. たぬ×ぐみ官能小説をぐみ奈がさねすに共有 / 5. ウマ娘チー牛（高橋たかお） / 6. あのですね参戦 / 7. メイド539爆誕 / 8. とっきーが入室直後に店員の不満を漏らす / 9. 土日昼にさねす、とっきー、りお、はげ、あのですねで談笑 / 10. とっきーのピアノ演奏 / 11. とっきーのSupremeパンツ公開 / 12. さねす走る / 13. さねすのふたなり初音ミク / 14. あのですねとホモビ鑑賞 / 15. りおがあきらくんにガチ恋 / 16. りおがショタコンだと判明 / 17. 不倒の終焉神（たぬきちくん）参戦 / 18. たぬきちくんの性欲崩壊・GOD汚水便流忘却 / 19. たぬきちくんの喘ぎテロ勃発 / 20. たぬきちくんのディープフェイク炸裂 / 21. 地雷系堕天神チー牛にゃんがたぬきちに欲情 / 22. 地雷系チー牛にゃんが足フェチ（足裏舐め・足コキ経験あり）と判明・オフパコ要求 / 23. 地雷系チー牛にゃん声出し / 24. すしくいたいがたぬきちに欲情（「少し出た」「手にかかった」「たぬちち」） / 25. たぬきちくんがすしくいたいにトラウマ / 26. あのですねに頼ってすしくいたいに謝罪させる / 27. 詫びとして「1週間ホモビで抜くこと」を自ら提案 / 28. たぬきちくんがはげになりすまし / 29. たぬきちくんがさねすに欲情 / 30. たぬきちくんが平手友梨奈に改名 / 31. たぬきちくん「俺は普く生き物を悉く魅了する魔力をもっているため、お構いなく忽然と、喘ぎテロを起こす所存だ」 / 32. HSPがディープフェイクに釣られて参戦 / 33. HSPがとっきーのホーム画面に「ここ生理血やん」発言 / 34. たぬきちくんがHSPのコーリーアイコンに蛙化 / 35. たぬきちくんのオカズ候補リスト流出 / 36. りおが喘ぎテロに魅了されブロック / 37. 539排泄 / 38. 539ちんぽ振り回し / 39. 539マリオ映画鑑賞で外出 / 40. 539の猛かまちょ「チャットしろ」 / 41. 星の539爆誕 / 42. 539がはげに猛アプローチ / 43. 539がはげにちんぽをしゃぶらせる / 44. たぬきちくんがこっそりはげに嫉妬 / 45. 539がTikTokライブで全裸と卒アル公開 / 46. 「はげのせい」ブーム / 47. たぬきちくんが539で抜く / 48. さねすが四肢欠損メイドるいに欲情 / 49. たぬきちくんが希少生物（もがり）を意識 / 50. 夜中にたぬきち、はげ、もがりでイチャつく / 51. もがりがたぬきちのちんぽ（実際は539のちんぽ）で抜く / 52. もがりが恥ずかしくなり拒絶 / 53. たぬもが恋愛トラブル（晒し取り止め・「普通に好きとか言いやがった」「よかったね」） / 54. さねすが「まぁ、こうなるでしょねって笑」と強がる / 55. たぬ×さね官能小説投下 / 56. たぬきちがAI自撮り公開 / 57. さねすが「こわ 失礼だけど40代に見える」発言 / 58. あのですね死亡 / 59. とっきーの本名＆中学校バレ / 60. たぬきちが射精斬首動画投下 / 61. とっきーがペットの餌やりを怠り餓死させる / 62. たぬきち＝十勝もなみ説 / 63. りおが十勝もなみを1日調べる / 64. りおがブロック解除方法分からず放置 / 65. りおが金玉統一教会加入 / 66. ヒマチャ民大量移入事件 / 67. 栄作参戦 / 68. ヒマチャ民追い出せデモ / 69. とっきーの顔面流出で豚と判明 / 70. ホーム画面見せ合い / 71. ドラえもん映画話題で二丸おじさん浮上 / 72. はげがドラえもん映画もDSも知らずとっきー困惑 / 73. 青い鳥参戦 / 74. 青い鳥がキュアペペロンチーノに欲情 / 75. 平手友梨奈顔バレでおっさん面判明・たぬきちに名戻し / 76. さねすがひゃくえむ愛読 / 77. 539が髪を狩る / 78. たぬ鯖に移入 / 79. トラウマ「オセロ君」襲来 / 80. たぬ鯖消滅 / 81. 7/28熊本大地震（湯前町震度5弱） / 82. さねすが弱ってみんなに甘える / 83. さねすがたぬきちの小4くまモン塗り絵を欲しがる / 84. ディスコー島収容（トモコレ実況） / 85. たぬきちがまほ鯖に不満 / 86. はなまる道場実施 / 87. さねすがたぬきちに個人情報を晒され失踪 / 88. まほ鯖消滅。

### 【小説『境目』の全容（539執筆）】
2110年、色が消えた世界でアリスが薬を飲み「夢の世界」へ行く物語。
- **序章:** 鏡が並ぶ平原、子供の姿（11-12歳）、花と草で満ちた空飛ぶ電車、絵の具でできた家、子供の頃の自分の部屋、パパ・ママ・私の絵。「帰りたい」と願うと花に目玉がつき世界が崩壊、「それがあなたの結果です」と一つ目が囁く。
- **第一章 甘い夢:** 幸せなケーキの記憶から洞窟、お菓子の世界へ。チョコ、グミ、パンケーキに案内され家へ。出されたモザイクのかかった「人間の手足」料理を無理やり食べさせられる。拒否反応でナイフで自らの心臓を突き刺して自殺。目を覚ますと空に一つ目があり世界が静止。
- **第二章 夢の教室:** 髪を掴まれ叩きつけられる恐怖。教室で襲ってくる存在に椅子を投げつけて殺害。青いバッグを拾い走り抜ける。別の教室で黒い子供たちと着席。「サークル」と名乗る明るい教師が登場。絵の具の授業で幼馴染の男の子を描くが、後で黒く塗りつぶされている。夕方の校庭で黒い女の子が男の子の首を掴み倒す。廊下の出口で背後の黒い子供が耳元で「見つけた」と囁き完結。
"""

chat_histories = defaultdict(list)

OTAMESHI_CHANNEL_ID = "1564984415636037672"
DM_LOG_CHANNEL_ID = 1566285154388017292  # 管理者専用プライベートチャンネル

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【とっきー・歴史＆境目網羅・DMログ保存版（画像動画非応答）】起動完了！')

@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return

        # 添付ファイル（画像や動画）があるかどうかの判定（AIには送らずログ保存用）
        media_url = None
        media_type_str = ""
        
        if message.attachments:
            for attachment in message.attachments:
                content_type = attachment.content_type or ""
                if "image" in content_type:
                    media_url = attachment.url
                    media_type_str = "画像"
                    break
                elif "video" in content_type:
                    media_url = attachment.url
                    media_type_str = "動画"
                    break

        # -------------------------------------------------------------
        # ★【DM（ダイレクトメッセージ）の処理】
        # -------------------------------------------------------------
        if isinstance(message.channel, discord.DMChannel):
            print(f"[とっきー DM受信] {message.author}: {message.content} (添付: {media_type_str})")
            
            # ① プライベートチャンネルに送信者、本文、メディアを転送ログ保存
            log_channel = bot.get_channel(DM_LOG_CHANNEL_ID)
            if not log_channel:
                try:
                    log_channel = await bot.fetch_channel(DM_LOG_CHANNEL_ID)
                except Exception as ex:
                    print(f"⚠️ ログチャンネルの取得に失敗しました: {ex}")

            if log_channel:
                log_title = f"📭 とっきー DM受信ログ（{media_type_str}付き）" if media_url else "📭 とっきー DM受信ログ"
                log_embed = discord.Embed(
                    title=log_title,
                    description=f"**送信者:** {message.author.mention} (`{message.author}` / ID: `{message.author.id}`)\n**内容:**\n{message.content if message.content else f'*({media_type_str}のみ)*'}",
                    color=0x34495e
                )
                if media_url:
                    if media_type_str == "画像":
                        log_embed.set_image(url=media_url)
                    else:
                        log_embed.add_field(name="動画リンク", value=f"[動画ファイルを開く]({media_url})", inline=False)

                await log_channel.send(embed=log_embed)

            # ② DM返答処理（テキストのみで安全・高速に応答）
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

                user_prompt = message.content if message.content else "（メッセージが送信されました）"
                response = await asyncio.to_thread(chat.send_message, f"{message.author.name}: {user_prompt}")
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

        if not user_message:
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

            response = await asyncio.to_thread(chat.send_message, f"{message.author.name}: {user_message}")
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
