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


# --- نصوص الاستبيان المترجمة للغات متعددة ---
TRANSLATIONS = {
    "ar": {
        "title": "📋 استبيان الأعضاء الجدد",
        "gender_ph": "اختر الجنس...",
        "gender_m": "ذكر",
        "gender_f": "أنثى",
        "age_ph": "اختر الفئة العمرية...",
        "country_ph": "اختر بلدك...",
        "saved": "✅ تم حفظ بياناتك ولغتك المفضلة بنجاح!",
    },
    "en": {
        "title": "📋 New Member Survey",
        "gender_ph": "Select Gender...",
        "gender_m": "Male",
        "gender_f": "Female",
        "age_ph": "Select Age Range...",
        "country_ph": "Select Country...",
        "saved": "✅ Your profile and language preference have been saved!",
    },
    "es": {
        "title": "📋 Encuesta de Nuevo Miembro",
        "gender_ph": "Seleccionar Género...",
        "gender_m": "Masculino",
        "gender_f": "Femenino",
        "age_ph": "Seleccionar Rango de Edad...",
        "country_ph": "Seleccionar País...",
        "saved": "✅ ¡Tu perfil y preferencia de idioma se han guardado!",
    },
    "fr": {
        "title": "📋 Sondage Nouvel Membre",
        "gender_ph": "Sélectionner le genre...",
        "gender_m": "Homme",
        "gender_f": "Femme",
        "age_ph": "Sélectionner la tranche d'âge...",
        "country_ph": "Sélectionner le pays...",
        "saved": "✅ Votre profil et langue préférée ont été enregistrés!",
    },
    "de": {
        "title": "📋 Umfrage für neue Mitglieder",
        "gender_ph": "Geschlecht auswählen...",
        "gender_m": "Männlich",
        "gender_f": "Weiblich",
        "age_ph": "Altersgruppe auswählen...",
        "country_ph": "Land auswählen...",
        "saved": "✅ Profil und Spracheinstellungen erfolgreich gespeichert!",
    },
    "tr": {
        "title": "📋 Yeni Üye Anketi",
        "gender_ph": "Cinsiyet Seçin...",
        "gender_m": "Erkek",
        "gender_f": "Kadın",
        "age_ph": "Yaş Aralığı Seçin...",
        "country_ph": "Ülke Seçin...",
        "saved": "✅ Profiliniz ve dil tercihiniz başarıyla kaydedildi!",
    },
    "ru": {
        "title": "📋 Опрос нового участника",
        "gender_ph": "Выберите пол...",
        "gender_m": "Мужской",
        "gender_f": "Женский",
        "age_ph": "Выберите возраст...",
        "country_ph": "Выберите страну...",
        "saved": "✅ Ваш профиль и языковые настройки сохранены!",
    },
    "zh-cn": {
        "title": "📋 新成员调查",
        "gender_ph": "选择性别...",
        "gender_m": "男",
        "gender_f": "女",
        "age_ph": "选择年龄段...",
        "country_ph": "选择国家...",
        "saved": "✅ 您的个人资料和语言偏好已保存！",
    },
    "ja": {
        "title": "📋 新規メンバーアンケート",
        "gender_ph": "性別を選択...",
        "gender_m": "男性",
        "gender_f": "女性",
        "age_ph": "年齢層を選択...",
        "country_ph": "国を選択...",
        "saved": "✅ プロフィールと言語設定が保存されました！",
    },
    "ko": {
        "title": "📋 신규 회원 설문조사",
        "gender_ph": "성별 선택...",
        "gender_m": "남성",
        "gender_f": "여성",
        "age_ph": "연령대 선택...",
        "country_ph": "국가 선택...",
        "saved": "✅ 프로필 및 언어 설정이 저장되었습니다!",
    },
}


# --- قوائم الاستبيان بعد اختيار اللغة ---
class GenderSelect(discord.ui.Select):

    def __init__(self, lang):
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(label=t["gender_m"], emoji="♂️", value="Male"),
            discord.SelectOption(
                label=t["gender_f"], emoji="♀️", value="Female"
            ),
        ]
        super().__init__(
            placeholder=t["gender_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "gender", self.values[0])
        await interaction.response.send_message("✅ Gender Saved!", ephemeral=True)


class AgeSelect(discord.ui.Select):

    def __init__(self, lang):
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(label="10 - 15", value="10-15"),
            discord.SelectOption(label="16 - 20", value="16-20"),
            discord.SelectOption(label="21 - 25", value="21-25"),
            discord.SelectOption(label="26 - 30", value="26-30"),
            discord.SelectOption(label="31 - 40", value="31-40"),
            discord.SelectOption(label="40+", value="40+"),
        ]
        super().__init__(
            placeholder=t["age_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "age", self.values[0])
        await interaction.response.send_message("✅ Age Saved!", ephemeral=True)


class CountrySelect(discord.ui.Select):

    def __init__(self, lang):
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(
                label="Saudi Arabia", emoji="🇸🇦", value="Saudi Arabia"
            ),
            discord.SelectOption(
                label="United Arab Emirates", emoji="🇦🇪", value="UAE"
            ),
            discord.SelectOption(label="Egypt", emoji="🇪🇬", value="Egypt"),
            discord.SelectOption(label="Yemen", emoji="🇾🇪", value="Yemen"),
            discord.SelectOption(label="Iraq", emoji="🇮🇶", value="Iraq"),
            discord.SelectOption(
                label="United States", emoji="🇺🇸", value="USA"
            ),
            discord.SelectOption(
                label="United Kingdom", emoji="🇬🇧", value="UK"
            ),
            discord.SelectOption(label="Turkey", emoji="🇹🇷", value="Turkey"),
            discord.SelectOption(
                label="Other / Global", emoji="🌐", value="Other"
            ),
        ]
        super().__init__(
            placeholder=t["country_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        update_user_field(interaction.user.id, "country", self.values[0])
        await interaction.response.send_message(
            "✅ Country Saved!", ephemeral=True
        )


class DetailsSurveyView(discord.ui.View):

    def __init__(self, lang):
        super().__init__(timeout=None)
        self.add_item(GenderSelect(lang))
        self.add_item(AgeSelect(lang))
        self.add_item(CountrySelect(lang))


# --- واجهة اختيار اللغة عبر 10 أزرار ---
class LanguageButtonView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def handle_lang_click(
        self, interaction: discord.Interaction, lang_code: str
    ):
        # 1. حفظ اللغة فوراً لتستخدم في الترجمة
        update_user_field(interaction.user.id, "language", lang_code)

        # 2. إظهار استبيان التفاصيل بلغة العضو
        t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
        embed = discord.Embed(
            title=t["title"],
            description="Complete your details below / أكمل بياناتك أدناه:",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(lang_code), ephemeral=True
        )

    @discord.ui.button(
        label="العربية",
        emoji="🇸🇦",
        style=discord.ButtonStyle.primary,
        custom_id="btn_ar",
    )
    async def btn_ar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ar")

    @discord.ui.button(
        label="English",
        emoji="🇺🇸",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_en",
    )
    async def btn_en(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "en")

    @discord.ui.button(
        label="Español",
        emoji="🇪🇸",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_es",
    )
    async def btn_es(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "es")

    @discord.ui.button(
        label="Français",
        emoji="🇫🇷",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_fr",
    )
    async def btn_fr(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "fr")

    @discord.ui.button(
        label="Deutsch",
        emoji="🇩🇪",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_de",
    )
    async def btn_de(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "de")

    @discord.ui.button(
        label="Türkçe",
        emoji="🇹🇷",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_tr",
    )
    async def btn_tr(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "tr")

    @discord.ui.button(
        label="Русский",
        emoji="🇷🇺",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_ru",
    )
    async def btn_ru(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ru")

    @discord.ui.button(
        label="中文",
        emoji="🇨🇳",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_zh",
    )
    async def btn_zh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "zh-cn")

    @discord.ui.button(
        label="日本語",
        emoji="🇯🇵",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_ja",
    )
    async def btn_ja(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ja")

    @discord.ui.button(
        label="한국어",
        emoji="🇰🇷",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_ko",
    )
    async def btn_ko(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ko")


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    bot.add_view(LanguageButtonView())
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


# الترحيب بالعضو عند انضمامه (إرسال في الخاص أولاً، وإذا تعذر يُرسل تنبيه)
@bot.event
async def on_member_join(member: discord.Member):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك",
        description="Select your preferred language to start the survey & enable instant translation!\nاختر لغتك المفضلة لبدء الاستبيان وتفعيل الترجمة الفورية!",
        color=discord.Color.blue(),
    )
    try:
        await member.send(embed=embed, view=LanguageButtonView())
    except discord.Forbidden:
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


# 🟢 أمر /survey للأعضاء (يحاول الإرسال في الخاص أولاً، وإن فشل يعرضه خفي في الشات نفسه)
@bot.tree.command(
    name="survey",
    description="اختر لغتك المفضلة وأكمل الاستبيان لتفعيل الترجمة الفورية",
)
async def user_request_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك",
        description="Select your preferred language to start the survey & enable instant translation!\nاختر لغتك المفضلة لبدء الاستبيان وتفعيل الترجمة الفورية!",
        color=discord.Color.blue(),
    )
    try:
        await interaction.user.send(embed=embed, view=LanguageButtonView())
        await interaction.response.send_message(
            "📬 تم إرسال قائمة اللغات في الرسائل الخاصة (DM)!", ephemeral=True
        )
    except discord.Forbidden:
        # إذا كانت الرسائل الخاصة مغلقة، يظهر الاستبيان فوراً في الشات للعضو فقط
        await interaction.response.send_message(
            embed=embed, view=LanguageButtonView(), ephemeral=True
        )


# --- أمر الأدمن لتثبيت اللوحة في قناة الترحيب ---
@bot.tree.command(
    name="setup-survey", description="إرسال لوحة اختيار اللغة في القناة (للآدمن)"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك المفضلة",
        description="Click your language button below to set up your profile and enable instant translation!\nاضغط على زر لغتك بالأسفل لضبط حسابك وتفعيل الترجمة الفورية!",
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=LanguageButtonView())
    await interaction.response.send_message(
        "✅ Language selection buttons sent successfully!", ephemeral=True
    )


# --- أمر الترجمة بالرد (/t) ---
@bot.tree.command(
    name="t", description="ترجمة الرسالة التي قمت بالرد عليها (Reply)"
)
@app_commands.describe(
    target_language="رمز اللغة المراد الترجمة إليها (اختياري)"
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


# --- أمر الترجمة بـ "كليك يمين" ---
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