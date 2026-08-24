import json
import os
import re
import discord
import firebase_admin
from firebase_admin import credentials, db
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive
from locales import TRANSLATIONS, get_text

# =========================================================
# إعداد Firebase Realtime Database
# =========================================================
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CREDENTIALS_RAW = os.getenv("FIREBASE_CREDENTIALS")

if FIREBASE_CREDENTIALS_RAW and FIREBASE_DB_URL:
    try:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_RAW)
        if "private_key" in cred_dict:
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
        print("✅ Connected to Firebase Realtime Database successfully!")
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
else:
    print("⚠️ FIREBASE_CREDENTIALS or FIREBASE_DB_URL not found!")

# =========================================================
# إعداد البوت
# =========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- إدارة البيانات عن طريق Firebase ---
def load_user_profiles():
    try:
        ref = db.reference("user_profiles")
        data = ref.get()
        return data if data else {}
    except Exception as e:
        print(f"❌ Error fetching Firebase data: {e}")
        return {}

def get_user_profile(user_id):
    try:
        ref = db.reference(f"user_profiles/{user_id}")
        data = ref.get()
        return data if data else {
            "gender": "Not Set",
            "age": "Not Set",
            "country": "Not Set",
            "language": "en",
        }
    except Exception as e:
        print(f"❌ Error fetching profile for user {user_id}: {e}")
        return {
            "gender": "Not Set",
            "age": "Not Set",
            "country": "Not Set",
            "language": "en",
        }

def update_user_field(user_id, field, value):
    try:
        user_str = str(user_id)
        ref = db.reference(f"user_profiles/{user_str}")
        user_data = ref.get()
        
        if not user_data:
            user_data = {
                "gender": "Not Set",
                "age": "Not Set",
                "country": "Not Set",
                "language": "en",
            }
        
        user_data[field] = value
        ref.set(user_data)
    except Exception as e:
        print(f"❌ Error updating Firebase data: {e}")

# --- ترجمة النصوص الذكية ---
def translate_smart_preserve_format(text: str, target_lang: str) -> str:
    """
    ترجمة النص سطرًا بسطر للمحافظة على التنسيق والسطور الفارغة.
    تترجم من أي لغة مصدريّة إلى اللغة المستهدفة.
    """
    if not text or not text.strip():
        return text

    translator = GoogleTranslator(source="auto", target=target_lang)
    lines = text.split("\n")
    translated_lines = []

    for line in lines:
        if not line.strip():
            translated_lines.append(line)
            continue

        try:
            translated_line = translator.translate(line)
            translated_lines.append(translated_line)
        except Exception as e:
            print(f"⚠️ Translation line error: {e}")
            translated_lines.append(line)

    return "\n".join(translated_lines)

# --- إدارة الرتب التلقائية ---
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
        return

    member = guild.get_member(interaction.user.id)
    if not member:
        try:
            member = await guild.fetch_member(interaction.user.id)
        except Exception:
            return

    roles_to_remove = [
        role
        for role in member.roles
        if role.name in category_options and role.name != selected_role_name
    ]
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove)
        except discord.Forbidden:
            pass

    target_role = discord.utils.get(guild.roles, name=selected_role_name)
    if not target_role:
        try:
            target_role = await guild.create_role(
                name=selected_role_name,
                color=role_color,
                reason="Auto-created profile role by Bot",
            )
        except discord.Forbidden:
            return

    if target_role not in member.roles:
        try:
            await member.add_roles(target_role)
        except discord.Forbidden:
            pass

# =========================================================
# القوائم والواجهات البرمجية
# =========================================================
GENDER_ROLES = ["♂️", "♀️"]
AGE_ROLES = ["10 - 15", "16 - 20", "21 - 25", "26 - 30", "31 - 40", "40+"]
COUNTRY_CODES = [
    "🇾🇪", "🇸🇦", "🇪🇬", "🇩🇿", "🇵🇸", "🇦🇪", "🇮🇶", "🇲🇦", "🇹🇳", "🇯🇴",
    "🇺🇸", "🇪🇸", "🇹🇷", "🇰🇷", "🇯🇵", "🇩🇪", "🇫🇷", "🇬🇧", "🇷🇺", "🇨🇳", "🇧🇬", "🇻🇳", "🌐"
]
COUNTRY_ROLES = COUNTRY_CODES


class GenderSelect(discord.ui.Select):
    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        options = [
            discord.SelectOption(
                label=get_text(lang, "gender_m"), emoji="♂️", value="♂️", default=(current_val == "♂️")
            ),
            discord.SelectOption(
                label=get_text(lang, "gender_f"), emoji="♀️", value="♀️", default=(current_val == "♀️")
            ),
        ]
        super().__init__(
            placeholder=get_text(lang, "gender_ph"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_gender = self.values[0]
        update_user_field(interaction.user.id, "gender", selected_gender)
        role_color = discord.Color.blue() if selected_gender == "♂️" else discord.Color.pink()

        await assign_profile_role(interaction, GENDER_ROLES, selected_gender, role_color)
        await interaction.response.send_message(
            get_text(self.lang, "saved_gender"), ephemeral=True
        )


class AgeSelect(discord.ui.Select):
    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        options = [
            discord.SelectOption(
                label=age, value=age, default=(current_val == age)
            ) for age in AGE_ROLES
        ]
        super().__init__(
            placeholder=get_text(lang, "age_ph"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_age = self.values[0]
        update_user_field(interaction.user.id, "age", selected_age)
        role_color = discord.Color.from_rgb(155, 89, 182)

        await assign_profile_role(interaction, AGE_ROLES, selected_age, role_color)
        await interaction.response.send_message(
            get_text(self.lang, "saved_age"), ephemeral=True
        )


class CountrySelect(discord.ui.Select):
    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        target_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get("countries", {})
        
        options = [
            discord.SelectOption(
                label=target_dict.get(code, code),
                emoji=code,
                value=code,
                default=(current_val == code)
            )
            for code in COUNTRY_CODES
        ]
        super().__init__(
            placeholder=get_text(lang, "country_ph"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_country = self.values[0]
        update_user_field(interaction.user.id, "country", selected_country)
        role_color = discord.Color.from_rgb(46, 204, 113)

        await assign_profile_role(interaction, COUNTRY_ROLES, selected_country, role_color)
        await interaction.response.send_message(
            get_text(self.lang, "saved_country"), ephemeral=True
        )


class DetailsSurveyView(discord.ui.View):
    def __init__(self, lang: str, user_profile: dict = None):
        super().__init__(timeout=None)
        user_profile = user_profile or {}
        
        curr_gender = user_profile.get("gender")
        curr_age = user_profile.get("age")
        curr_country = user_profile.get("country")

        self.add_item(GenderSelect(lang, curr_gender))
        self.add_item(AgeSelect(lang, curr_age))
        self.add_item(CountrySelect(lang, curr_country))


class LanguageButtonView(discord.ui.View):
    def __init__(self, current_lang: str = None):
        super().__init__(timeout=None)
        if current_lang:
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == f"btn_{current_lang}":
                    item.style = discord.ButtonStyle.success

    async def handle_lang_click(self, interaction: discord.Interaction, lang_code: str):
        update_user_field(interaction.user.id, "language", lang_code)
        embed = discord.Embed(
            title=get_text(lang_code, "title"),
            description=get_text(lang_code, "survey_desc"),
            color=discord.Color.green(),
        )
        user_data = get_user_profile(interaction.user.id)
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(lang_code, user_data), ephemeral=True
        )

    @discord.ui.button(label="English", emoji="🇺🇸", style=discord.ButtonStyle.secondary, custom_id="btn_en")
    async def btn_en(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "en")

    @discord.ui.button(label="العربية", emoji="🇸🇦", style=discord.ButtonStyle.secondary, custom_id="btn_ar")
    async def btn_ar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "ar")

    @discord.ui.button(label="日本語", emoji="🇯🇵", style=discord.ButtonStyle.secondary, custom_id="btn_ja")
    async def btn_ja(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "ja")

    @discord.ui.button(label="Español", emoji="🇪🇸", style=discord.ButtonStyle.secondary, custom_id="btn_es")
    async def btn_es(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "es")

    @discord.ui.button(label="한국어", emoji="🇰🇷", style=discord.ButtonStyle.secondary, custom_id="btn_ko")
    async def btn_ko(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "ko")

    @discord.ui.button(label="Български", emoji="🇧🇬", style=discord.ButtonStyle.secondary, custom_id="btn_bg")
    async def btn_bg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "bg")

    @discord.ui.button(label="Tiếng Việt", emoji="🇻🇳", style=discord.ButtonStyle.secondary, custom_id="btn_vi")
    async def btn_vi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_lang_click(interaction, "vi")

class ProfileManageView(discord.ui.View):
    def __init__(self, user_lang: str, user_data: dict = None):
        super().__init__(timeout=None)
        self.user_lang = user_lang
        self.user_data = user_data or {}
        
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "btn_edit_profile":
                    item.label = get_text(user_lang, "edit_btn")
                elif item.custom_id == "btn_change_lang":
                    item.label = get_text(user_lang, "change_lang_btn")

    @discord.ui.button(label="Edit Profile", style=discord.ButtonStyle.primary, custom_id="btn_edit_profile")
    async def edit_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=get_text(self.user_lang, "title"),
            description=get_text(self.user_lang, "survey_desc"),
            color=discord.Color.blue(),
        )
        user_data = get_user_profile(interaction.user.id)
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(self.user_lang, user_data), ephemeral=True
        )

    @discord.ui.button(label="Change Language", style=discord.ButtonStyle.secondary, custom_id="btn_change_lang")
    async def change_language(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=get_text(self.user_lang, "lang_title"),
            description=get_text(self.user_lang, "lang_desc"),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(
            embed=embed, view=LanguageButtonView(current_lang=self.user_lang), ephemeral=True
        )

# =========================================================
# الأحداث والأوامر
# =========================================================
@bot.event
async def on_ready():
    try:
        await bot.load_extension("games")
    except Exception as e:
        print(f"⚠️ Extension load status: {e}")

    bot.add_view(LanguageButtonView())
    await bot.tree.sync()
    print(f"Logged in as {bot.user} & Slash commands synced!")


@bot.event
async def on_member_join(member: discord.Member):
    embed = discord.Embed(
        title="🌐 Choose Your Language",
        description="Select your preferred language to start setting up your profile & enable instant translation!",
        color=discord.Color.blue(),
    )
    try:
        await member.send(embed=embed, view=LanguageButtonView())
    except discord.Forbidden:
        pass


@bot.tree.command(name="profile", description="View & Edit your profile settings")
async def view_profile(interaction: discord.Interaction):
    user_data = get_user_profile(interaction.user.id)
    lang = user_data.get("language", "en")

    country_code = user_data.get("country", "Not Set")
    country_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get("countries", {})
    display_country = country_dict.get(
        country_code, 
        country_code if country_code != "Not Set" else get_text(lang, "not_set")
    )

    gender_val = user_data.get("gender", "Not Set")
    if gender_val == "♂️":
        display_gender = get_text(lang, "gender_m")
    elif gender_val == "♀️":
        display_gender = get_text(lang, "gender_f")
    else:
        display_gender = get_text(lang, "not_set")

    age_val = user_data.get("age", "Not Set")
    if age_val == "Not Set":
        age_val = get_text(lang, "not_set")

    embed = discord.Embed(
        title=get_text(lang, "profile_title"),
        description=get_text(lang, "profile_desc"),
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name=f"🌐 {get_text(lang, 'lang_label')}", value=lang.upper(), inline=True)
    embed.add_field(name=f"👤 {get_text(lang, 'gender_label')}", value=display_gender, inline=True)
    embed.add_field(name=f"🎂 {get_text(lang, 'age_label')}", value=age_val, inline=True)
    embed.add_field(name=f"🚩 {get_text(lang, 'country_label')}", value=display_country, inline=True)

    await interaction.response.send_message(
        embed=embed, view=ProfileManageView(lang, user_data), ephemeral=True
    )


# --- الأمر النصي للترجمة بالرد (Prefix Command !t) ---
@bot.command(name="t")
async def quick_translate_prefix(ctx: commands.Context, target_language: str = None):
    user_info = get_user_profile(ctx.author.id)
    user_lang = user_info.get("language", "en")
    final_lang = target_language.lower().strip() if target_language else user_lang

    # التحقق من وجود رد (Reply) على رسالة
    if not ctx.message.reference or not ctx.message.reference.message_id:
        await ctx.send(get_text(user_lang, "reply_error"), delete_after=5)
        return

    try:
        # جلب الرسالة المردود عليها مباشرة برقم الـ ID
        target_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except Exception as e:
        print(f"⚠️ Error fetching target message: {e}")
        await ctx.send(get_text(user_lang, "reply_error"), delete_after=5)
        return

    if not target_msg or not target_msg.content:
        await ctx.send(get_text(user_lang, "reply_error"), delete_after=5)
        return

    try:
        translated_text = translate_smart_preserve_format(target_msg.content, final_lang)
        # إرسال الرسالة المترجمة بالرد على أمر المستخدم
        await ctx.reply(translated_text, mention_author=False)
    except Exception as e:
        err_msg = get_text(user_lang, "trans_error")
        await ctx.send(f"{err_msg} {e}", delete_after=5)


# --- أمر سياق الخيارات المباشر (Context Menu) ---
@bot.tree.context_menu(name="Translate to My Language")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    user_info = get_user_profile(interaction.user.id)
    target_lang = user_info.get("language", "en")

    if not message.content:
        await interaction.response.send_message(
            get_text(target_lang, "no_text_error"), ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        translated_text = translate_smart_preserve_format(message.content, target_lang)
        await interaction.followup.send(translated_text, ephemeral=True)
    except Exception as e:
        err_msg = get_text(target_lang, "trans_error")
        await interaction.followup.send(f"{err_msg} {e}", ephemeral=True)

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN missing!")