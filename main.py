import json
import os
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# إعداد البوت مع تفعيل Members Intent
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # مطلوب للتعرف على انضمام الأعضاء الجدد

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "user_profiles.json"


# --- إدارة البيانات ---
def load_user_profiles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_user_profile(user_id, gender, age, country, language):
    data = load_user_profiles()
    data[str(user_id)] = {
        "gender": gender,
        "age": age,
        "country": country,
        "language": language,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- نموذج الاستبيان (Modal) ---
class SurveyModal(discord.ui.Modal, title="📋 استبيان انضمام عضو جديد"):
    gender = discord.ui.TextInput(
        label="النع/الجنس",
        placeholder="ذكر / أنثى",
        required=True,
        max_length=10,
    )

    age = discord.ui.TextInput(
        label="العمر",
        placeholder="مثال: 22",
        required=True,
        max_length=3,
    )

    country = discord.ui.TextInput(
        label="البلد",
        placeholder="مثال: السعودية / مصر / اليمن",
        required=True,
        max_length=50,
    )

    language = discord.ui.TextInput(
        label="اللغة الأساسية/المفضلة",
        placeholder="مثال: ar أو en",
        required=True,
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # حفظ البيانات عند الإرسال
        save_user_profile(
            user_id=interaction.user.id,
            gender=self.gender.value.strip(),
            age=self.age.value.strip(),
            country=self.country.value.strip(),
            language=self.language.value.strip().lower(),
        )

        await interaction.response.send_message(
            f"✅ شكراً لك {interaction.user.mention}! تم حفظ بياناتك بنجاح في البوت.",
            ephemeral=True,
        )


# --- زر فتح الاستبيان ---
class SurveyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)  # جعل الزر يعيش دائماً

    @discord.ui.button(
        label="تعبئة الاستبيان 📝",
        style=discord.ButtonStyle.primary,
        custom_id="start_survey_btn",
    )
    async def open_survey(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(SurveyModal())


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    bot.add_view(SurveyView())  # تسجيل الزر الدائم
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


# الترحيب بالعضو عند انضمامه وإرسال الاستبيان له على الخاص (DM)
@bot.event
async def on_member_join(member: discord.Member):
    try:
        embed = discord.Embed(
            title=f"أهلاً بك في السيرفر {member.name}! 👋",
            description="يرجى الضغط على الزر أدناه لتعبئة استبيان الترحيب القصير وتحديد بياناتك لخدمتك بشكل أفضل.",
            color=discord.Color.green(),
        )
        await member.send(embed=embed, view=SurveyView())
    except discord.Forbidden:
        # إذا كانت الرسائل الخاصة مغلقة لدى العضو
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


# --- أمر يدوي لإرسال الزر في قناة الترحيب إن أردت ---
@bot.tree.command(
    name="setup-survey",
    description="إرسال لوحة الاستبيان في القناة الحالية (للآدمن)",
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 استبيان الأعضاء الجدد",
        description="اضغط على الزر أدناه لتحديد جنسك، عمرك، بلدك، ولغتك المفضلة.",
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=SurveyView())
    await interaction.response.send_message(
        "✅ تم إرسال لوحة الاستبيان بنجاح!", ephemeral=True
    )


# --- 1️⃣ أمر Slash لتحديد اللغة المفضلة ---
@bot.tree.command(
    name="set-language", description="اختر لغتك الأم/المفضلة للترجمة إليها"
)
@app_commands.describe(language_code="رمز اللغة (مثال: ar, en, es)")
async def set_language(interaction: discord.Interaction, language_code: str):
    lang = language_code.lower().strip()
    # تحديث اللغة في ملف البروفايلات
    data = load_user_profiles()
    user_id_str = str(interaction.user.id)

    if user_id_str in data:
        data[user_id_str]["language"] = lang
    else:
        data[user_id_str] = {
            "gender": "غير محدد",
            "age": "غير محدد",
            "country": "غير محدد",
            "language": lang,
        }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await interaction.response.send_message(
        f"✅ تم حفظ لغتك المفضلة إلى: `{lang}`", ephemeral=True
    )


# --- 2️⃣ أمر Slash لعرض رموز اللغات ---
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


# --- 3️⃣ أمر السلاش السريع للترجمة بالرد (/t) ---
@bot.tree.command(
    name="t", description="ترجمة الرسالة التي قمت بالرد عليها (Reply)"
)
@app_commands.describe(
    target_language="رمز اللغة المراد الترجمة إليها (اختياري، الافتراضي هو لغتك الأم)"
)
async def quick_translate(
    interaction: discord.Interaction, target_language: str = None
):
    channel = interaction.channel
    target_msg = None

    if interaction.data.get("resolved", {}).get("messages"):
        target_msg = list(interaction.data["resolved"]["messages"].values())[0]

    try:
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
    except Exception:
        pass

    if not target_msg or not target_msg.content:
        await interaction.response.send_message(
            "⚠️ يرجى استخدام الأمر `/t` كـ **رد (Reply)** على الرسالة التي تريد ترجمتها!",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    if target_language:
        final_lang = target_language.lower().strip()
    else:
        profiles = load_user_profiles()
        user_info = profiles.get(str(interaction.user.id), {})
        final_lang = user_info.get("language", "ar")

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


# --- 4️⃣ أمر Context Menu للترجمة كليك يمين ---
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
    profiles = load_user_profiles()
    user_info = profiles.get(str(interaction.user.id), {})
    target_lang = user_info.get("language", "ar")

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

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")