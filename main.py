import json
import os
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "user_profiles.json"


# --- إدارة البيانات ---
def load_user_profiles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_user_field(user_id, field, value):
    data = load_user_profiles()
    user_str = str(user_id)
    if user_str not in data:
        data[user_str] = {
            "gender": "Not Set",
            "age": "Not Set",
            "country": "Not Set",
            "language": "ar",
        }
    data[user_str][field] = value
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- قائمة اختيار الجنس ---
class GenderSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="Male", emoji="♂️", value="Male"),
            discord.SelectOption(label="Female", emoji="♀️", value="Female"),
        ]
        super().__init__(
            placeholder="Select Gender...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "gender", self.values[0])
        await interaction.response.send_message(
            f"✅ Gender set to: **{self.values[0]}**", ephemeral=True
        )


# --- قائمة اختيار العمر ---
class AgeSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="10 - 15 years", value="10-15"),
            discord.SelectOption(label="16 - 20 years", value="16-20"),
            discord.SelectOption(label="21 - 25 years", value="21-25"),
            discord.SelectOption(label="26 - 30 years", value="26-30"),
            discord.SelectOption(label="31 - 40 years", value="31-40"),
            discord.SelectOption(label="40+ years", value="40+"),
        ]
        super().__init__(
            placeholder="Select Age Range...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "age", self.values[0])
        await interaction.response.send_message(
            f"✅ Age set to: **{self.values[0]}**", ephemeral=True
        )


# --- قائمة اختيار الدولة ---
class CountrySelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Saudi Arabia", emoji="🇸🇦", value="Saudi Arabia"
            ),
            discord.SelectOption(
                label="United Arab Emirates",
                emoji="🇦🇪",
                value="United Arab Emirates",
            ),
            discord.SelectOption(label="Egypt", emoji="🇪🇬", value="Egypt"),
            discord.SelectOption(label="Yemen", emoji="🇾🇪", value="Yemen"),
            discord.SelectOption(label="Iraq", emoji="🇮🇶", value="Iraq"),
            discord.SelectOption(label="Jordan", emoji="🇯🇴", value="Jordan"),
            discord.SelectOption(label="Morocco", emoji="🇲🇦", value="Morocco"),
            discord.SelectOption(label="Algeria", emoji="🇩🇿", value="Algeria"),
            discord.SelectOption(
                label="United States", emoji="🇺🇸", value="United States"
            ),
            discord.SelectOption(
                label="United Kingdom", emoji="🇬🇧", value="United Kingdom"
            ),
            discord.SelectOption(
                label="Turkey", emoji="🇹🇷", value="Turkey"
            ),
            discord.SelectOption(label="Other / Global", emoji="🌐", value="Other"),
        ]
        super().__init__(
            placeholder="Select Country...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "country", self.values[0])
        await interaction.response.send_message(
            f"✅ Country set to: **{self.values[0]}**", ephemeral=True
        )


# --- قائمة اختيار اللغة المفضلة ---
class LanguageSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Arabic (العربية)", emoji="🇸🇦", value="ar"
            ),
            discord.SelectOption(
                label="English", emoji="🇺🇸", value="en"
            ),
            discord.SelectOption(
                label="Spanish (Español)", emoji="🇪🇸", value="es"
            ),
            discord.SelectOption(
                label="French (Français)", emoji="🇫🇷", value="fr"
            ),
            discord.SelectOption(
                label="German (Deutsch)", emoji="🇩🇪", value="de"
            ),
            discord.SelectOption(
                label="Turkish (Türkçe)", emoji="🇹🇷", value="tr"
            ),
            discord.SelectOption(
                label="Russian (Русский)", emoji="🇷🇺", value="ru"
            ),
            discord.SelectOption(
                label="Japanese (日本語)", emoji="🇯🇵", value="ja"
            ),
        ]
        super().__init__(
            placeholder="Select Preferred Language...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "language", self.values[0])
        await interaction.response.send_message(
            f"✅ Preferred Language set to: `{self.values[0]}`", ephemeral=True
        )


# --- واجهة الاستبيان الكاملة (View) ---
class SurveyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        # إضافة القوائم الأربع للواجهة
        self.add_item(GenderSelect())
        self.add_item(AgeSelect())
        self.add_item(CountrySelect())
        self.add_item(LanguageSelect())


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    bot.add_view(SurveyView())
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


@bot.event
async def on_member_join(member: discord.Member):
    try:
        embed = discord.Embed(
            title="👋 Welcome / أهلاً بك!",
            description="Please select your details from the dropdown menus below:\nيرجى اختيار بياناتك من القوائم المنسدلة أدناه:",
            color=discord.Color.blue(),
        )
        await member.send(embed=embed, view=SurveyView())
    except discord.Forbidden:
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


@bot.tree.command(
    name="setup-survey",
    description="إرسال قائمة الاستبيان بالمنسدلات في القناة الحالية (للآدمن)",
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Welcome Survey / استبيان الترحيب",
        description="Select your Gender, Age, Country, and Preferred Language below:\nاختر جنسك، عمرك، بلدك، ولغتك المفضلة من القوائم:",
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=SurveyView())
    await interaction.response.send_message(
        "✅ Survey panel sent successfully!", ephemeral=True
    )


# --- 1️⃣ أمر Slash لتحديد اللغة المفضلة ---
@bot.tree.command(
    name="set-language", description="اختر لغتك الأم/المفضلة للترجمة إليها"
)
@app_commands.describe(language_code="رمز اللغة (مثال: ar, en, es)")
async def set_language(interaction: discord.Interaction, language_code: str):
    lang = language_code.lower().strip()
    update_user_field(interaction.user.id, "language", lang)
    await interaction.response.send_message(
        f"✅ Saved target language to: `{lang}`", ephemeral=True
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
        "🟢 **`es`** - Spanish\n"
        "🟢 **`fr`** - French\n"
        "🟢 **`de`** - German\n"
        "🟢 **`tr`** - Turkish\n"
        "🟢 **`ru`** - Russian\n"
        "🟢 **`ja`** - Japanese"
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