import json
import os
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive  # استدعاء خادم الويب

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "user_languages.json"


def load_user_languages():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_user_language(user_id, lang_code):
    data = load_user_languages()
    data[str(user_id)] = lang_code
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


# 1️⃣ أمر Slash لتحديد اللغة المفضلة
@bot.tree.command(
    name="set-language", description="اختر لغتك الأم/المفضلة للترجمة إليها"
)
@app_commands.describe(language_code="رمز اللغة (مثال: ar, en, es)")
async def set_language(interaction: discord.Interaction, language_code: str):
    lang = language_code.lower().strip()
    save_user_language(interaction.user.id, lang)
    await interaction.response.send_message(
        f"✅ تم حفظ لغتك المفضلة إلى: `{lang}`", ephemeral=True
    )


# 2️⃣ أمر Slash لعرض رموز اللغات
@bot.tree.command(
    name="languages", description="عرض قائمة برموز اللغات المتاحة للترجمة"
)
async def list_languages(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Supported Languages & Language Codes",
        description="استخدم أحد الرموز أدناه مع الأمر `/set-language`",
        color=discord.Color.blue(),
    )
    languages_list = (
        "🟢 **`ar`** - Arabic (العربية)\n"
        "🟢 **`en`** - English\n"
        "🟢 **`es`** - Spanish (Español)\n"
        "🟢 **`fr`** - French (Français)\n"
        "🟢 **`de`** - German (Deutsch)\n"
        "🟢 **`tr`** - Turkish (Türkçe)\n"
        "🟢 **`ru`** - Russian (Русский)\n"
        "🟢 **`zh-cn`** - Chinese Simplified\n"
        "🟢 **`ja`** - Japanese\n"
        "🟢 **`ko`** - Korean"
    )
    embed.add_field(
        name="Popular Language Codes", value=languages_list, inline=False
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# 3️⃣ أمر السلاش السريع للترجمة بالرد (/t)
@bot.tree.command(
    name="t", description="ترجمة الرسالة التي قمت بالرد عليها (Reply)"
)
@app_commands.describe(
    target_language="رمز اللغة المراد الترجمة إليها (اختياري، الافتراضي هو لغتك الأم)"
)
async def quick_translate(
    interaction: discord.Interaction, target_language: str = None
):
    # التأكد من أن المستخدم يرتكز على رسالة معينة عبر الرد
    referenced_msg = interaction.message.reference if interaction.message else None

    # في أوامر الـ Slash لا تتوفر reference مباشرة داخل interaction، لذا نجلب الرسالة المردود عليها من القناة
    channel = interaction.channel
    target_msg = None

    # التحقق من آخر رسائل القناة لمعرفة الرسالة المردود عليها إن وجدت
    if interaction.data.get("resolved", {}).get("messages"):
        # جلب الرسالة في حال تم التمرير من الواجهة
        target_msg = list(interaction.data["resolved"]["messages"].values())[0]

    # جلب الرسالة المراد ترجمتها عبر المرجع
    try:
        # البحث عن الرسالة المرجعية في الشات
        async for msg in channel.history(limit=5):
            if msg.id == interaction.id:
                continue
            # إذا استجاب للرد مباشرة
            if (
                msg.author.id == interaction.user.id
                and msg.reference
                and msg.reference.message_id
            ):
                target_msg = await channel.fetch_message(
                    msg.reference.message_id
                )
                break
    except Exception:
        pass

    # إذا لم نجد الرد عبر الهستوري المحلي، نتحقق من أحدث رسالة قام المستخدم بالرد عليها
    if not target_msg:
        # محاولة جلب مرجع الرسالة المباشر من خلال جلب آخر رسالة للمستخدم
        async for msg in channel.history(limit=10):
            if (
                msg.author.id == interaction.user.id
                and msg.reference
                and msg.reference.message_id
            ):
                target_msg = await channel.fetch_message(
                    msg.reference.message_id
                )
                break

    if not target_msg or not target_msg.content:
        await interaction.response.send_message(
            "⚠️ يرجى استخدام الأمر `/t` كـ **رد (Reply)** على الرسالة التي تريد ترجمتها!",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    # تحديد اللغة الهدف (إما المدخلة أو اللغة الأم)
    if target_language:
        final_lang = target_language.lower().strip()
    else:
        user_langs = load_user_languages()
        final_lang = user_langs.get(str(interaction.user.id), "ar")

    try:
        translated_text = GoogleTranslator(
            source="auto", target=final_lang
        ).translate(target_msg.content)
        response_text = (
            f"🌐 **الترجمة إلى ({final_lang}):**\n```{translated_text}```"
        )
        await interaction.followup.send(response_text, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True
        )


# 4️⃣ أمر Context Menu للترجمة كليك يمين
@bot.tree.context_menu(name="Translate to My Language")
async def translate_message(
    interaction: discord.Interaction, message: discord.Message
):
    if not message.content:
        await interaction.response.send_message(
            "⚠️ هذه الرسالة لا تحتوي على نص لترجمته.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    user_langs = load_user_languages()
    target_lang = user_langs.get(str(interaction.user.id), "ar")

    try:
        translated_text = GoogleTranslator(
            source="auto", target=target_lang
        ).translate(message.content)
        response_text = (
            f"🌐 **الترجمة إلى ({target_lang}):**\n```{translated_text}```"
        )
        await interaction.followup.send(response_text, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True
        )


# تشغيل خادم إبقاء البوت حياً
keep_alive()

# جلب التوكن بأمان من متغيرات البيئة
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")