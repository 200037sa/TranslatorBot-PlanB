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

# نصوص الاستبيان المترجمة للغات الشائعة
TRANSLATIONS = {
    "ar": {
        "title": "📋 استبيان الترحيب",
        "gender_title": "اختر الجنس:",
        "male": "ذكر",
        "female": "أنثى",
        "age_title": "اختر الفئة العمرية:",
        "country_title": "اختر مكان الإقامة/المنطقة:",
        "done": "✅ تم حفظ جميع بياناتك بنجاح! يمكنك الآن استخدام أمر الترجمة `/t` في أي وقت.",
    },
    "en": {
        "title": "📋 Welcome Survey",
        "gender_title": "Select your Gender:",
        "male": "Male",
        "female": "Female",
        "age_title": "Select Age Range:",
        "country_title": "Select Region/Country:",
        "done": "✅ All your details have been saved! You can now use `/t` for instant translation.",
    },
    "es": {
        "title": "📋 Encuesta de Bienvenida",
        "gender_title": "Selecciona tu Género:",
        "male": "Masculino",
        "female": "Femenino",
        "age_title": "Selecciona Rango de Edad:",
        "country_title": "Selecciona Región:",
        "done": "✅ ¡Datos guardados! Ya puedes usar `/t` para traducir.",
    },
    "fr": {
        "title": "📋 Enquête d'accueil",
        "gender_title": "Sélectionnez votre Genre:",
        "male": "Homme",
        "female": "Femme",
        "age_title": "Sélectionnez la Tranche d'âge:",
        "country_title": "Sélectionnez la Région:",
        "done": "✅ Données enregistrées ! Vous pouvez utiliser `/t` pour traduire.",
    },
    "de": {
        "title": "📋 Willkommensumfrage",
        "gender_title": "Wähle dein Geschlecht:",
        "male": "Männlich",
        "female": "Weiblich",
        "age_title": "Wähle Altersgruppe:",
        "country_title": "Wähle Region:",
        "done": "✅ Daten gespeichert! Du kannst jetzt `/t` zum Übersetzen nutzen.",
    },
    "tr": {
        "title": "📋 Hoş Geldiniz Anketİ",
        "gender_title": "Cinsiyetinizi Seçin:",
        "male": "Erkek",
        "female": "Kadın",
        "age_title": "Yaş Aralığını Seçin:",
        "country_title": "Bölgenizi Seçin:",
        "done": "✅ Bilgileriniz kaydedildi! Artık çeviri için `/t` kullanabilirsiniz.",
    },
    "ru": {
        "title": "📋 Приветственный опрос",
        "gender_title": "Выберите ваш пол:",
        "male": "Мужской",
        "female": "Женский",
        "age_title": "Выберите возраст:",
        "country_title": "Выберите регион:",
        "done": "✅ Данные сохранены! Теперь вы можете использовать `/t` для перевода.",
    },
    "zh-cn": {
        "title": "📋 欢迎调查",
        "gender_title": "选择你的性别：",
        "male": "男",
        "female": "女",
        "age_title": "选择年龄段：",
        "country_title": "选择地区：",
        "done": "✅ 数据已保存！您现在可以使用 `/t` 进行即时翻译。",
    },
    "ja": {
        "title": "📋 ウェルカムアンケート",
        "gender_title": "性別を選択してください：",
        "male": "男性",
        "female": "女性",
        "age_title": "年齢層を選択してください：",
        "country_title": "地域を選択してください：",
        "done": "✅ 設定が保存されました！`/t` で翻訳機能を利用できます。",
    },
    "ko": {
        "title": "📋 환영 설문조사",
        "gender_title": "성별을 선택하세요:",
        "male": "남성",
        "female": "여성",
        "age_title": "연령대를 선택하세요:",
        "country_title": "지역을 선택하세요:",
        "done": "✅ 정보가 저장되었습니다! 이제 `/t` 명령어로 번역할 수 있습니다.",
    },
}


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


# --- 2️⃣ أزرار المرحلة الثانية: البيانات المترجمة ---
class ProfileSurveyView(discord.ui.View):

    def __init__(self, lang_code: str):
        super().__init__(timeout=None)
        self.lang = lang_code if lang_code in TRANSLATIONS else "en"
        self.texts = TRANSLATIONS[self.lang]
        self.selected_gender = None
        self.selected_age = None
        self.selected_country = None

        # إضافة أزرار الجنس
        self.add_item(
            SurveyButton(
                label=self.texts["male"],
                emoji="♂️",
                category="gender",
                value="Male",
            )
        )
        self.add_item(
            SurveyButton(
                label=self.texts["female"],
                emoji="♀️",
                category="gender",
                value="Female",
            )
        )

        # إضافة أزرار العمر
        for age_range in ["10-17", "18-24", "25-34", "35+"]:
            self.add_item(
                SurveyButton(
                    label=age_range, category="age", value=age_range
                )
            )

        # إضافة أزرار المناطق
        regions = [
            ("🇸🇦 Middle East / 🗺️", "Middle East"),
            ("🇪🇺 Europe", "Europe"),
            ("🇺🇸 Americas", "Americas"),
            ("🌏 Asia / Global", "Asia/Global"),
        ]
        for label, val in regions:
            self.add_item(
                SurveyButton(label=label, category="country", value=val)
            )


class SurveyButton(discord.ui.Button):

    def __init__(
        self,
        label: str,
        category: str,
        value: str,
        emoji: str = None,
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
        )
        self.category = category
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, self.category, self.value)
        self.style = discord.ButtonStyle.success  # تغيير لون الزر المختار للأخضر
        await interaction.response.send_message(
            f"✅ Saved: **{self.value}**", ephemeral=True
        )


# --- 1️⃣ أزرار المرحلة الأولى: اختيار 10 لغات شائعة ---
class LanguageSelectionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        languages = [
            ("العربية", "🇸🇦", "ar"),
            ("English", "🇺🇸", "en"),
            ("Español", "🇪🇸", "es"),
            ("Français", "🇫🇷", "fr"),
            ("Deutsch", "🇩🇪", "de"),
            ("Türkçe", "🇹🇷", "tr"),
            ("Русский", "🇷🇺", "ru"),
            ("简体中文", "🇨🇳", "zh-cn"),
            ("日本語", "🇯🇵", "ja"),
            ("한국어", "🇰🇷", "ko"),
        ]

        for label, emoji, code in languages:
            self.add_item(LanguageButton(label=label, emoji=emoji, code=code))


class LanguageButton(discord.ui.Button):

    def __init__(self, label: str, emoji: str, code: str):
        super().__init__(
            label=label, emoji=emoji, style=discord.ButtonStyle.primary
        )
        self.code = code

    async def callback(self, interaction: discord.Interaction):
        # 1. حفظ اللغة فوراً لتفعيل الترجمة المباشرة
        update_user_field(interaction.user.id, "language", self.code)

        # 2. جلب النصوص المترجمة للغة المختارة
        lang_texts = TRANSLATIONS.get(self.code, TRANSLATIONS["en"])

        embed = discord.Embed(
            title=lang_texts["title"],
            description=(
                f"🌐 Language saved to: **{self.code}**\n\n"
                f"**1. {lang_texts['gender_title']}**\n"
                f"**2. {lang_texts['age_title']}**\n"
                f"**3. {lang_texts['country_title']}**"
            ),
            color=discord.Color.green(),
        )

        # 3. فتح المرحلة الثانية بالأزرار المترجمة
        await interaction.response.send_message(
            embed=embed,
            view=ProfileSurveyView(self.code),
            ephemeral=True,
        )


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    bot.add_view(LanguageSelectionView())
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


@bot.event
async def on_member_join(member: discord.Member):
    try:
        embed = discord.Embed(
            title="🌐 Choose Your Language / اختر لغتك",
            description="Please select your preferred language below to start the survey & enable instant translations:\nاختر لغتك المفضلة من الأزرار أدناه للبدء وتفعيل الترجمة الفورية:",
            color=discord.Color.blue(),
        )
        await member.send(embed=embed, view=LanguageSelectionView())
    except discord.Forbidden:
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


@bot.tree.command(
    name="survey",
    description="عرض استبيان اللغة والبيانات الشخصية بالرسائل الخاصة (DM)",
)
async def user_request_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك",
        description="Select your language to customize your survey & enable instant translation:\nاختر لغتك لتخصيص الاستبيان وتفعيل الترجمة الفورية:",
        color=discord.Color.blue(),
    )
    try:
        await interaction.user.send(embed=embed, view=LanguageSelectionView())
        await interaction.response.send_message(
            "📬 تم إرسال الاستبيان لك في الخاصة (DM)!", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ تعذّر الإرسال، يرجى فتح الرسائل الخاصة (DMs) في إعدادات الحساب.",
            ephemeral=True,
        )


@bot.tree.command(
    name="setup-survey", description="إرسال لوحة اللغات في القناة (للآدمن)"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك المفضلة",
        description="Click your language button to get started & activate `/t` translation:\nاضغط على زر لغتك للبدء وتفعيل الترجمة الفورية:",
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=LanguageSelectionView())
    await interaction.response.send_message(
        "✅ Survey panel sent!", ephemeral=True
    )


# --- أمر الترجمة السريع (/t) ---
@bot.tree.command(
    name="t", description="ترجمة الرسالة التي قمت بالرد عليها (Reply)"
)
@app_commands.describe(
    target_language="رمز اللغة المراد الترجمة إليها (اختياري، الافتراضي لغتك المحفوظة)"
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
            "⚠️ يرجى استخدام الأمر `/t` كـ **رد (Reply)** على الرسالة المراد ترجمتها!",
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
        await interaction.followup.send(
            f"🌐 **الترجمة إلى ({final_lang}):**\n```{translated_text}```",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True
        )


# --- أمر الترجمة بـ Click Right ---
@bot.tree.context_menu(name="Translate to My Language")
async def translate_message(
    interaction: discord.Interaction, message: discord.Message
):
    if not message.content:
        await interaction.response.send_message(
            "⚠️ لا يوجد نص لترجمته.", ephemeral=True
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
        await interaction.followup.send(
            f"🌐 **الترجمة إلى ({target_lang}):**\n```{translated_text}```",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True
        )


keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN!")