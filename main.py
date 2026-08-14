import json
import os
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive
import motor.motor_asyncio  # استخدام motor بدلاً من pymongo للـ Async

# =========================================================
# الاتصال بقاعدة بيانات MongoDB Atlas بشكل أزامني (Async)
# =========================================================
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("⚠️ تحذير: لم يتم العثور على MONGO_URI في متغيرات البيئة!")

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo_client["bot_database"]
users_col = db["user_profiles"]


# --- إدارة البيانات باستخدام Async MongoDB ---
async def load_user_profile(user_id):
    """جلب بيانات مستخدم واحد فقط لتقليل الضغط والتأخير"""
    user_str = str(user_id)
    doc = await users_col.find_one({"_id": user_str})
    if not doc:
        return {
            "gender": "Not Set",
            "age": "Not Set",
            "country": "Not Set",
            "language": "en",
        }
    return {
        "gender": doc.get("gender", "Not Set"),
        "age": doc.get("age", "Not Set"),
        "country": doc.get("country", "Not Set"),
        "language": doc.get("language", "en"),
    }


async def update_user_field(user_id, field, value):
    user_str = str(user_id)
    await users_col.update_one(
        {"_id": user_str},
        {"$set": {field: value}},
        upsert=True
    )


# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# --- وظيفة مساعدة لإدارة الرتب التلقائية ---
async def assign_profile_role(
    interaction: discord.Interaction,
    category_options: list,
    selected_role_name: str,
    role_color: discord.Color = discord.Color.default(),
):
    guild = interaction.guild

    if not guild:
        for g in interaction.client.guilds:
            member_in_g = g.get_member(interaction.user.id)
            if member_in_g:
                guild = g
                break

    if not guild:
        print(f"❌ لم يتم العثور على سيرفر مشترك للعضو {interaction.user.name}.")
        return

    member = guild.get_member(interaction.user.id)
    if not member:
        try:
            member = await guild.fetch_member(interaction.user.id)
        except Exception as e:
            print(f"❌ تعذر جلب العضو من السيرفر: {e}")
            return

    # إزالة أي رتبة سابقة تنتمي لنفس الفئة
    roles_to_remove = [
        role for role in member.roles
        if role.name in category_options and role.name != selected_role_name
    ]
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove)
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية Manage Roles لإزالة الرتب.")

    # البحث عن الرتبة أو إنشاؤها
    target_role = discord.utils.get(guild.roles, name=selected_role_name)
    if not target_role:
        try:
            target_role = await guild.create_role(
                name=selected_role_name,
                color=role_color,
                reason="Auto-created profile role by Survey Bot",
            )
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية Manage Roles لإنشاء الرتبة.")
            return

    # إسناد الرتبة
    if target_role not in member.roles:
        try:
            await member.add_roles(target_role)
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية إضافة الرتب للعضو.")


# --- نصوص الواجهات باللغات المعتمدة ---
TRANSLATIONS = {
    "ar": {
        "title": "📋 استبيان الأعضاء",
        "gender_ph": "اختر الجنس...",
        "gender_m": "ذكر ♂️",
        "gender_f": "أنثى ♀️",
        "age_ph": "اختر الفئة العمرية...",
        "country_ph": "اختر بلدك...",
        "saved_gender": "✅ تم حفظ الجنس وإسناد الرتبة ♂️/♀️",
        "saved_age": "✅ تم حفظ الفئة العمرية وإسناد الرتبة",
        "saved_country": "✅ تم حفظ الدولة وإسناد رتبة علم الدولة",
        "profile_title": "👤 ملفك الشخصي",
        "profile_desc": "إليك بياناتك الحالية المخزنة في النظام:",
        "lang_label": "اللغة",
        "gender_label": "الجنس",
        "age_label": "العمر",
        "country_label": "الدولة",
        "edit_btn": "✏️ تعديل البيانات",
        "change_lang_btn": "🌐 تغيير اللغة فقط",
    },
    "en": {
        "title": "📋 Member Profile Setup",
        "gender_ph": "Select Gender...",
        "gender_m": "Male ♂️",
        "gender_f": "Female ♀️",
        "age_ph": "Select Age Range...",
        "country_ph": "Select Country...",
        "saved_gender": "✅ Gender saved and role assigned!",
        "saved_age": "✅ Age range saved and role assigned!",
        "saved_country": "✅ Country saved and flag role assigned!",
        "profile_title": "👤 Your Profile",
        "profile_desc": "Here are your current profile settings:",
        "lang_label": "Language",
        "gender_label": "Gender",
        "age_label": "Age Range",
        "country_label": "Country",
        "edit_btn": "✏️ Edit Profile",
        "change_lang_btn": "🌐 Change Language Only",
    },
    "ja": {
        "title": "📋 メンバープロフィール設定",
        "gender_ph": "性別を選択...",
        "gender_m": "男性 ♂️",
        "gender_f": "女性 ♀️",
        "age_ph": "年齢層を選択...",
        "country_ph": "国を選択...",
        "saved_gender": "✅ 性別が保存されロールが付与されました！",
        "saved_age": "✅ 年齢層が保存されロールが付与されました！",
        "saved_country": "✅ 国が保存され国旗ロールが付与されました！",
        "profile_title": "👤 あなたのプロフィール",
        "profile_desc": "現在設定されている情報です:",
        "lang_label": "言語",
        "gender_label": "性別",
        "age_label": "年齢",
        "country_label": "国",
        "edit_btn": "✏️ プロフィール編集",
        "change_lang_btn": "🌐 言語のみ変更",
    },
    "es": {
        "title": "📋 Configuración de Perfil",
        "gender_ph": "Seleccionar Género...",
        "gender_m": "Masculino ♂️",
        "gender_f": "Femenino ♀️",
        "age_ph": "Seleccionar Rango de Edad...",
        "country_ph": "Seleccionar País...",
        "saved_gender": "✅ ¡Género guardado y rol asignado!",
        "saved_age": "✅ ¡Rango de edad guardado y rol asignado!",
        "saved_country": "✅ ¡País guardado y rol de bandera asignado!",
        "profile_title": "👤 Tu Perfil",
        "profile_desc": "Aquí están tus datos actuales:",
        "lang_label": "Idioma",
        "gender_label": "Género",
        "age_label": "Edad",
        "country_label": "País",
        "edit_btn": "✏️ Editar Perfil",
        "change_lang_btn": "🌐 Cambiar solo Idioma",
    },
    "ko": {
        "title": "📋 프로필 설정",
        "gender_ph": "성별 선택...",
        "gender_m": "남성 ♂️",
        "gender_f": "여성 ♀️",
        "age_ph": "연령대 선택...",
        "country_ph": "국가 선택...",
        "saved_gender": "✅ 성별이 저장되고 역할이 부여되었습니다!",
        "saved_age": "✅ 연령대가 저장되고 역할이 부여되었습니다!",
        "saved_country": "✅ 국가가 저장되고 국기 역할이 부여되었습니다!",
        "profile_title": "👤 내 프로필",
        "profile_desc": "현재 저장된 프로필 정보입니다:",
        "lang_label": "언어",
        "gender_label": "성별",
        "age_label": "연령대",
        "country_label": "국가",
        "edit_btn": "✏️ 프로필 수정",
        "change_lang_btn": "🌐 언어만 변경",
    },
}

GENDER_ROLES = ["♂️", "♀️"]

AGE_ROLES = [
    "10 - 15",
    "16 - 20",
    "21 - 25",
    "26 - 30",
    "31 - 40",
    "40+",
]

COUNTRY_OPTIONS = [
    {"label": "اليمن / Yemen", "emoji": "🇾🇪", "value": "🇾🇪"},
    {"label": "السعودية / KSA", "emoji": "🇸🇦", "value": "🇸🇦"},
    {"label": "مصر / Egypt", "emoji": "🇪🇬", "value": "🇪🇬"},
    {"label": "الجزائر / Algeria", "emoji": "🇩🇿", "value": "🇩🇿"},
    {"label": "فلسطين / Palestine", "emoji": "🇵🇸", "value": "🇵🇸"},
    {"label": "الإمارات / UAE", "emoji": "🇦🇪", "value": "🇦🇪"},
    {"label": "العراق / Iraq", "emoji": "🇮🇶", "value": "🇮🇶"},
    {"label": "المغرب / Morocco", "emoji": "🇲🇦", "value": "🇲🇦"},
    {"label": "تونس / Tunisia", "emoji": "🇹🇳", "value": "🇹🇳"},
    {"label": "الأردن / Jordan", "emoji": "🇯🇴", "value": "🇯🇴"},
    {"label": "أمريكا / USA", "emoji": "🇺🇸", "value": "🇺🇸"},
    {"label": "إسبانيا / Spain", "emoji": "🇪🇸", "value": "🇪🇸"},
    {"label": "تركيا / Turkey", "emoji": "🇹🇷", "value": "🇹🇷"},
    {"label": "كوريا / Korea", "emoji": "🇰🇷", "value": "🇰🇷"},
    {"label": "اليابان / Japan", "emoji": "🇯🇵", "value": "🇯🇵"},
    {"label": "ألمانيا / Germany", "emoji": "🇩🇪", "value": "🇩🇪"},
    {"label": "فرنسا / France", "emoji": "🇫🇷", "value": "🇫🇷"},
    {"label": "المملكة المتحدة / UK", "emoji": "🇬🇧", "value": "🇬🇧"},
    {"label": "روسيا / Russia", "emoji": "🇷🇺", "value": "🇷🇺"},
    {"label": "الصين / China", "emoji": "🇨🇳", "value": "🇨🇳"},
    {"label": "دولة أخرى / Other", "emoji": "🌐", "value": "🌐"},
]

COUNTRY_ROLES = [c["value"] for c in COUNTRY_OPTIONS]


# --- القوائم المنسدلة ---
class GenderSelect(discord.ui.Select):

    def __init__(self, lang):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(label=t["gender_m"], emoji="♂️", value="♂️"),
            discord.SelectOption(label=t["gender_f"], emoji="♀️", value="♀️"),
        ]
        super().__init__(
            placeholder=t["gender_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_gender = self.values[0]
        await update_user_field(interaction.user.id, "gender", selected_gender)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = (
            discord.Color.blue()
            if selected_gender == "♂️"
            else discord.Color.pink()
        )

        await assign_profile_role(
            interaction, GENDER_ROLES, selected_gender, role_color
        )
        await interaction.followup.send(t["saved_gender"], ephemeral=True)


class AgeSelect(discord.ui.Select):

    def __init__(self, lang):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(label=age, value=age) for age in AGE_ROLES
        ]
        super().__init__(
            placeholder=t["age_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_age = self.values[0]
        await update_user_field(interaction.user.id, "age", selected_age)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = discord.Color.from_rgb(155, 89, 182)

        await assign_profile_role(
            interaction, AGE_ROLES, selected_age, role_color
        )
        await interaction.followup.send(t["saved_age"], ephemeral=True)


class CountrySelect(discord.ui.Select):

    def __init__(self, lang):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        options = [
            discord.SelectOption(
                label=c["label"], emoji=c["emoji"], value=c["value"]
            )
            for c in COUNTRY_OPTIONS
        ]
        super().__init__(
            placeholder=t["country_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_country = self.values[0]
        await update_user_field(interaction.user.id, "country", selected_country)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = discord.Color.from_rgb(46, 204, 113)

        await assign_profile_role(
            interaction, COUNTRY_ROLES, selected_country, role_color
        )
        await interaction.followup.send(t["saved_country"], ephemeral=True)


class DetailsSurveyView(discord.ui.View):

    def __init__(self, lang):
        super().__init__(timeout=None)
        self.add_item(GenderSelect(lang))
        self.add_item(AgeSelect(lang))
        self.add_item(CountrySelect(lang))


# --- واجهة أزرار اختيار اللغة الأساسية ---
class LanguageButtonView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def handle_lang_click(
        self, interaction: discord.Interaction, lang_code: str
    ):
        await interaction.response.defer(ephemeral=True)
        await update_user_field(interaction.user.id, "language", lang_code)
        t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
        embed = discord.Embed(
            title=t["title"],
            description="Fill your profile options below:",
            color=discord.Color.green(),
        )
        await interaction.followup.send(
            embed=embed, view=DetailsSurveyView(lang_code), ephemeral=True
        )

    @discord.ui.button(
        label="English",
        emoji="🇺🇸",
        style=discord.ButtonStyle.primary,
        custom_id="btn_en",
    )
    async def btn_en(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "en")

    @discord.ui.button(
        label="العربية",
        emoji="🇸🇦",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_ar",
    )
    async def btn_ar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ar")

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
        label="한국어",
        emoji="🇰🇷",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_ko",
    )
    async def btn_ko(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_lang_click(interaction, "ko")


# --- واجهة إدارة البروفايل ---
class ProfileManageView(discord.ui.View):

    def __init__(self, user_lang: str):
        super().__init__(timeout=None)
        self.user_lang = user_lang

    @discord.ui.button(
        label="✏️ Edit Profile",
        style=discord.ButtonStyle.primary,
        custom_id="btn_edit_profile",
    )
    async def edit_profile(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        t = TRANSLATIONS.get(self.user_lang, TRANSLATIONS["en"])
        embed = discord.Embed(
            title=t["title"],
            description="Select your updated information:",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(self.user_lang), ephemeral=True
        )

    @discord.ui.button(
        label="🌐 Change Language",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_change_lang",
    )
    async def change_language(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌐 Choose Your Language",
            description="Select your preferred language below:",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(
            embed=embed, view=LanguageButtonView(), ephemeral=True
        )


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    try:
        await bot.load_extension("games")
    except Exception as e:
        print(f"⚠️ لم يتم تحميل إضافة الألعاب: {e}")

    bot.add_view(LanguageButtonView())
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح ({len(synced)} أمر)!")


@bot.event
async def on_member_join(member: discord.Member):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك",
        description="Select your preferred language to start setting up your profile & enable instant translation!",
        color=discord.Color.blue(),
    )
    try:
        await member.send(embed=embed, view=LanguageButtonView())
    except discord.Forbidden:
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


# --- أمر عرض/تعديل البروفايل الخاص بالعضو ---
@bot.tree.command(
    name="profile", description="عرض وتعديل بيانات ملفك الشخصي ولغتك المفضلة"
)
async def view_profile(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # جلب بيانات العضو الحالي فقط secara Async
    user_data = await load_user_profile(interaction.user.id)

    lang = user_data.get("language", "en")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    embed = discord.Embed(
        title=t["profile_title"],
        description=t["profile_desc"],
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(
        url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    embed.add_field(
        name=f"🌐 {t['lang_label']}",
        value=lang.upper(),
        inline=True,
    )
    embed.add_field(
        name=f"👤 {t['gender_label']}",
        value=user_data.get("gender", "Not Set"),
        inline=True,
    )
    embed.add_field(
        name=f"🎂 {t['age_label']}",
        value=user_data.get("age", "Not Set"),
        inline=True,
    )
    embed.add_field(
        name=f"🚩 {t['country_label']}",
        value=user_data.get("country", "Not Set"),
        inline=True,
    )

    await interaction.followup.send(
        embed=embed, view=ProfileManageView(lang), ephemeral=True
    )


@bot.tree.command(
    name="survey", description="فتح استبيان اختيار اللغة والبيانات"
)
async def user_request_survey(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك",
        description="Select your preferred language to start!",
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(
        embed=embed, view=LanguageButtonView(), ephemeral=True
    )


@bot.tree.command(
    name="setup-survey", description="إرسال لوحة اختيار اللغة في القناة (للإدارة)"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_survey(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🌐 Choose Your Language / اختر لغتك المفضلة",
        description="Click your language button below to set up your profile and enable instant translation!",
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=LanguageButtonView())
    await interaction.followup.send(
        "✅ Language selection buttons sent successfully!", ephemeral=True
    )


# --- أمر الترجمة السريعة بالرد (/t) ---
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
        user_info = await load_user_profile(interaction.user.id)
        final_lang = user_info.get("language", "en")

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


# --- أمر الترجمة بالزر الأيمن للفأرة ---
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
    user_info = await load_user_profile(interaction.user.id)
    target_lang = user_info.get("language", "en")

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


keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")