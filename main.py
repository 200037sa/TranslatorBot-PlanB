import json
import os
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

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


def save_user_profile(user_id, **kwargs):
    data = load_user_profiles()
    user_key = str(user_id)
    if user_key not in data:
        data[user_key] = {}
    
    # تحديث القيم الممررة فقط
    for key, value in kwargs.items():
        data[user_key][key] = value

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- واجهة الاستبيان المنسدلة التفاعلية (Interactive Select View) ---
class ComprehensiveSurveyView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300) # صلاحية الواجهة 5 دقائق
        self.user_id = user_id
        self.selected_gender = None
        self.selected_age = None
        self.selected_country = None
        self.selected_lang = None

    # 1️⃣ قائمة اختيار الجنس
    @discord.ui.select(
        placeholder="1. Select your Gender / اختر جنسك...",
        options=[
            discord.SelectOption(label="Male", value="Male", emoji="👨"),
            discord.SelectOption(label="Female", value="Female", emoji="👩"),
        ]
    )
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاستبيان مخصص لشخص آخر.", ephemeral=True)
            return
        self.selected_gender = select.values[0]
        await interaction.response.send_message(f"✅ Selected Gender: **{self.selected_gender}**", ephemeral=True)

    # 2️⃣ قائمة اختيار العمر
    @discord.ui.select(
        placeholder="2. Select your Age / اختر عمرك...",
        options=[
            discord.SelectOption(label="10 - 15 years old", value="10-15", emoji="👶"),
            discord.SelectOption(label="16 - 20 years old", value="16-20", emoji="🧑"),
            discord.SelectOption(label="21 - 25 years old", value="21-25", emoji="🧔"),
            discord.SelectOption(label="26 - 30 years old", value="26-30", emoji="👨"),
            discord.SelectOption(label="31 - 40 years old", value="31-40", emoji="💼"),
            discord.SelectOption(label="40+ years old", value="40+", emoji="👓"),
        ]
    )
    async def select_age(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاستبيان مخصص لشخص آخر.", ephemeral=True)
            return
        self.selected_age = select.values[0]
        await interaction.response.send_message(f"✅ Selected Age: **{self.selected_age}**", ephemeral=True)

    # 3️⃣ قائمة اختيار البلد
    @discord.ui.select(
        placeholder="3. Select your Country / اختر بلدك...",
        options=[
            discord.SelectOption(label="Saudi Arabia", value="Saudi Arabia", emoji="🇸🇦"),
            discord.SelectOption(label="Egypt", value="Egypt", emoji="🇪🇬"),
            discord.SelectOption(label="Yemen", value="Yemen", emoji="🇾🇪"),
            discord.SelectOption(label="United Arab Emirates", value="UAE", emoji="🇦🇪"),
            discord.SelectOption(label="Kuwait", value="Kuwait", emoji="🇰🇼"),
            discord.SelectOption(label="Iraq", value="Iraq", emoji="🇮🇶"),
            discord.SelectOption(label="Jordan", value="Jordan", emoji="🇯🇴"),
            discord.SelectOption(label="Morocco", value="Morocco", emoji="🇲🇦"),
            discord.SelectOption(label="United States", value="USA", emoji="🇺🇸"),
            discord.SelectOption(label="United Kingdom", value="UK", emoji="🇬🇧"),
            discord.SelectOption(label="Other Country", value="Other", emoji="🌐"),
        ]
    )
    async def select_country(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاستبيان مخصص لشخص آخر.", ephemeral=True)
            return
        self.selected_country = select.values[0]
        await interaction.response.send_message(f"✅ Selected Country: **{self.selected_country}**", ephemeral=True)

    # 4️⃣ قائمة اختيار اللغة الأم
    @discord.ui.select(
        placeholder="4. Select your Preferred Language / لغتك المفضلة...",
        options=[
            discord.SelectOption(label="Arabic (العربية)", value="ar", emoji="🇸🇦"),
            discord.SelectOption(label="English", value="en", emoji="🇺🇸"),
            discord.SelectOption(label="Spanish (Español)", value="es", emoji="🇪🇸"),
            discord.SelectOption(label="French (Français)", value="fr", emoji="🇫🇷"),
            discord.SelectOption(label="German (Deutsch)", value="de", emoji="🇩🇪"),
            discord.SelectOption(label="Turkish (Türkçe)", value="tr", emoji="🇹🇷"),
            discord.SelectOption(label="Russian (Русский)", value="ru", emoji="🇷🇺"),
            discord.SelectOption(label="Japanese (日本語)", value="ja", emoji="🇯🇵"),
        ]
    )
    async def select_language(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاستبيان مخصص لشخص آخر.", ephemeral=True)
            return
        self.selected_lang = select.values[0]
        await interaction.response.send_message(f"✅ Selected Language: **{self.selected_lang}**", ephemeral=True)

    # 🟢 زر إرسال وحفظ الاستبيان النهائي
    @discord.ui.button(label="Submit Survey / حفظ البيانات ✅", style=discord.ButtonStyle.success, row=4)
    async def submit_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاستبيان مخصص لشخص آخر.", ephemeral=True)
            return

        if not all([self.selected_gender, self.selected_age, self.selected_country, self.selected_lang]):
            await interaction.response.send_message("⚠️ يرجى الاختيار من جميع القوائم الأربع أعلاه قبل الضغط على حفظ!", ephemeral=True)
            return

        # حفظ البيانات في الملف مباشرة وتعيين اللغة للترجمة تلقائياً
        save_user_profile(
            user_id=interaction.user.id,
            gender=self.selected_gender,
            age=self.selected_age,
            country=self.selected_country,
            language=self.selected_lang
        )

        embed = discord.Embed(
            title="🎉 Survey Completed / تم حفظ البيانات بنجاح!",
            description=(
                f"**Gender:** {self.selected_gender}\n"
                f"**Age:** {self.selected_age}\n"
                f"**Country:** {self.selected_country}\n"
                f"**Default Translation Language:** `{self.selected_lang}`\n\n"
                f"💡 يمكنك الآن استخدام أمر الترجمة `/t` مباشرة دون الحاجة لأي إعدادات إضافية!"
            ),
            color=discord.Color.green()
        )
        
        # تعطيل الخيارات بعد الحفظ
        self.stop()
        await interaction.response.send_message(embed=embed, ephemeral=True)


# --- زر فتح الاستبيان للأعضاء الجدد ---
class OpenSurveyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Survey / تعبئة الاستبيان 📝", style=discord.ButtonStyle.primary, custom_id="start_dropdown_survey")
    async def open_survey(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ComprehensiveSurveyView(user_id=interaction.user.id)
        embed = discord.Embed(
            title="📋 Welcome Survey / استبيان الترحيب",
            description="يرجى الاختيار من القوائم المنسدلة التالية ثم اضغط على **Submit Survey** عند الانتهاء:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    bot.add_view(OpenSurveyButtonView())
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!")


# الترحيب بالعضو عند الانضمام عبر الخاص (DM)
@bot.event
async def on_member_join(member: discord.Member):
    try:
        embed = discord.Embed(
            title=f"Welcome / أهلاً بك {member.name}! 👋",
            description="يرجى الضغط على الزر أدناه لتعبئة الاستبيان المنسدل القصير وتحديد لغتك المفضلة للترجمة الفورية.",
            color=discord.Color.blue()
        )
        await member.send(embed=embed, view=OpenSurveyButtonView())
    except discord.Forbidden:
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


# --- 1️⃣ أمر السلاش الخاص بملء الاستبيان للأعضاء القدامى أو الحاليين (/survey) ---
@bot.tree.command(name="survey", description="فتح استبيان الانضمام المنسدل لتحديد لغتك وبياناتك")
async def trigger_survey(interaction: discord.Interaction):
    view = ComprehensiveSurveyView(user_id=interaction.user.id)
    embed = discord.Embed(
        title="📋 Welcome Survey / استبيان البيانات واللغة المفضلة",
        description="اختر بياناتك ولغتك المفضلة من القوائم أدناه ثم اضغط **Submit Survey**:",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# --- 2️⃣ أمر Slash لتحديد اللغة المفضلة (اختياري) ---
@bot.tree.command(name="set-language", description="تغيير لغتك الأم/المفضلة للترجمة إليها")
@app_commands.describe(language_code="رمز اللغة (مثال: ar, en, es)")
async def set_language(interaction: discord.Interaction, language_code: str):
    lang = language_code.lower().strip()
    save_user_profile(user_id=interaction.user.id, language=lang)
    await interaction.response.send_message(f"✅ تم تحديث لغتك المفضلة إلى: `{lang}`", ephemeral=True)


# --- 3️⃣ أمر Slash لعرض رموز اللغات ---
@bot.tree.command(name="languages", description="عرض قائمة برموز اللغات المتاحة للترجمة")
async def list_languages(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Supported Languages & Codes",
        description="استخدم القائمة أدناه للتعرف على الرموز",
        color=discord.Color.blue()
    )
    languages_list = (
        "🟢 **`ar`** - Arabic\n🟢 **`en`** - English\n🟢 **`es`** - Spanish\n"
        "🟢 **`fr`** - French\n🟢 **`de`** - German\n🟢 **`tr`** - Turkish\n"
        "🟢 **`ru`** - Russian\n🟢 **`ja`** - Japanese"
    )
    embed.add_field(name="Language Codes", value=languages_list, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- 4️⃣ أمر الترجمة السريعة بالرد (/t) ---
@bot.tree.command(name="t", description="ترجمة الرسالة التي قمت بالرد عليها (Reply)")
@app_commands.describe(target_language="رمز اللغة المراد الترجمة إليها (اختياري)")
async def quick_translate(interaction: discord.Interaction, target_language: str = None):
    channel = interaction.channel
    target_msg = None

    if interaction.data.get("resolved", {}).get("messages"):
        target_msg = list(interaction.data["resolved"]["messages"].values())[0]

    try:
        async for msg in channel.history(limit=10):
            if msg.author.id == interaction.user.id and msg.reference and msg.reference.message_id:
                target_msg = await channel.fetch_message(msg.reference.message_id)
                break
    except Exception:
        pass

    if not target_msg or not target_msg.content:
        await interaction.response.send_message("⚠️ يرجى استخدام الأمر `/t` كـ **رد (Reply)** على الرسالة!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if target_language:
        final_lang = target_language.lower().strip()
    else:
        profiles = load_user_profiles()
        user_info = profiles.get(str(interaction.user.id), {})
        # جلب اللغة المحددة في الاستبيان تلقائياً (الافتراضي ar)
        final_lang = user_info.get("language", "ar")

    try:
        translated_text = GoogleTranslator(source="auto", target=final_lang).translate(target_msg.content)
        response_text = f"🌐 **الترجمة إلى ({final_lang}):**\n```{translated_text}```"
        await interaction.followup.send(response_text, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True)


# --- 5️⃣ أمر Context Menu للترجمة كليك يمين ---
@bot.tree.context_menu(name="Translate to My Language")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    if not message.content:
        await interaction.response.send_message("⚠️ هذه الرسالة لا تحتوي على نص.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    profiles = load_user_profiles()
    user_info = profiles.get(str(interaction.user.id), {})
    target_lang = user_info.get("language", "ar")

    try:
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(message.content)
        response_text = f"🌐 **الترجمة إلى ({target_lang}):**\n```{translated_text}```"
        await interaction.followup.send(response_text, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True)


keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")