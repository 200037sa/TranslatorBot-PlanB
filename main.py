import json
import os
import re
import urllib.parse
import discord
import requests
import firebase_admin
from firebase_admin import credentials, db
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# =========================================================
# إعداد Firebase Realtime Database
# =========================================================
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CREDENTIALS_RAW = os.getenv("FIREBASE_CREDENTIALS")

if FIREBASE_CREDENTIALS_RAW and FIREBASE_DB_URL:
    try:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_RAW)
        
        # إصلاح أسطر المفتاح الخاص في حال تم تعويض \n كنص عادي
        if "private_key" in cred_dict:
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        print("✅ تم الاتصال بـ Firebase Realtime Database بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء تهيئة Firebase: {e}")
else:
    print("⚠️ لم يتم العثور على FIREBASE_CREDENTIALS أو FIREBASE_DB_URL في متغيرات البيئة!")
    
# =========================================================
# إعداد البوت
# =========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# منطق ترجمة العربيزي (Hybrid Transliteration Engine)
# =========================================================

WORD_DICTIONARY = {
    "tmam": "تمام",
    "shokran": "شكرا",
    "mabrook": "مبروك",
}

CHAR_MAP = [
    ('kh', 'خ'), ('gh', 'غ'), ('ch', 'ش'), ('sh', 'ش'),
    ('th', 'ث'), ('dh', 'ذ'),
    ('2', 'أ'),  ('3', 'ع'),  ('5', 'خ'),  ('6', 'ط'),
    ('7', 'ح'),  ('8', 'ق'),  ('9', 'ق'),
    ('a', 'ا'),  ('b', 'ب'),  ('t', 'ت'),  ('g', 'ج'),
    ('j', 'ج'),  ('h', 'ه'),  ('d', 'د'),  ('r', 'ر'),
    ('z', 'ز'),  ('s', 'س'),  ('q', 'ق'),  ('k', 'ك'),
    ('l', 'ل'),  ('m', 'م'),  ('n', 'ن'),  ('w', 'و'),
    ('o', 'و'),  ('u', 'و'),  ('y', 'ي'),  ('i', 'ي'),
    ('e', 'ي'),  ('f', 'ف'),  ('p', 'ب'),  ('v', 'ف'),
    ('x', 'كس')
]

def get_arabic_from_yamli(word: str) -> str:
    """البحث أونلاين عن طريق Yamli بدون الحاجة لـ API Key"""
    try:
        encoded_word = urllib.parse.quote(word)
        url = f"https://api.yamli.com/api/transliterate/adapter=yamli&pt=1&account_id=0&text={encoded_word}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            r_data = data.get("r", "")
            if r_data:
                first_match = r_data.split("|")[0].split("/")[0]
                return first_match
    except Exception as e:
        print(f"⚠️ Yamli search error for word '{word}': {e}")
    return None

def translate_word_arabizi(word: str) -> str:
    clean_word = word.lower()
    if clean_word in WORD_DICTIONARY:
        return WORD_DICTIONARY[clean_word]
    
    online_result = get_arabic_from_yamli(clean_word)
    if online_result:
        return online_result
    
    translated = clean_word
    for eng, ara in CHAR_MAP:
        translated = translated.replace(eng, ara)
    return translated

def process_arabizi_text(text: str) -> str:
    """تحويل نص العربيزي إلى نص عربي مع الحفاظ على الفواصل والرموز"""
    words = re.findall(r'\b\w+\b|\s+|[^\w\s]', text)
    result = []
    
    for item in words:
        if item.isalnum() and not item.isdigit() and not re.search(r'[\u0600-\u06FF]', item):
            result.append(translate_word_arabizi(item))
        else:
            result.append(item)
            
    return "".join(result)

# --- إدارة البيانات عن طريق Firebase ---
def load_user_profiles():
    try:
        ref = db.reference("user_profiles")
        data = ref.get()
        return data if data else {}
    except Exception as e:
        print(f"❌ خطأ عند جلب البيانات من Firebase: {e}")
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
        print(f"❌ خطأ عند جلب بيانات المستخدم {user_id}: {e}")
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
        print(f"❌ خطأ عند تحديث البيانات في Firebase: {e}")

# --- وظيفة ذكية لترجمة النصوص المخلطة والحفاظ على التنسيق والإيموجي ---
def translate_smart_preserve_format(text: str, target_lang: str) -> str:
    """ترجمة النصوص إلى اللغة الهدف مع الحفاظ على التنسيق والرموز."""
    if not text:
        return text

    if target_lang == "ar":
        return text

    translator = GoogleTranslator(source="auto", target=target_lang)
    lines = text.split("\n")
    translated_lines = []

    arabic_pattern = re.compile(r"[\u0600-\u06FF]")

    for line in lines:
        if not line.strip() or not arabic_pattern.search(line):
            translated_lines.append(line)
            continue

        try:
            translated_line = translator.translate(line)
            translated_lines.append(translated_line)
        except Exception:
            translated_lines.append(line)

    return "\n".join(translated_lines)

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

    roles_to_remove = [
        role
        for role in member.roles
        if role.name in category_options and role.name != selected_role_name
    ]
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove)
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية Manage Roles لإزالة الرتب.")

    target_role = discord.utils.get(guild.roles, name=selected_role_name)
    if not target_role:
        try:
            target_role = await guild.create_role(
                name=selected_role_name,
                color=role_color,
                reason="Auto-created profile role by Bot",
            )
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية Manage Roles لإنشاء الرتبة.")
            return

    if target_role not in member.roles:
        try:
            await member.add_roles(target_role)
        except discord.Forbidden:
            print("❌ البوت لا يملك صلاحية إضافة الرتب للعضو.")

# =========================================================
# الترجمة الشاملة للنصوص والدول (i18n)
# =========================================================
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
        "not_set": "غير محدد",
        "countries": {
            "🇾🇪": "اليمن", "🇸🇦": "السعودية", "🇪🇬": "مصر", "🇩🇿": "الجزائر",
            "🇵🇸": "فلسطين", "🇦🇪": "الإمارات", "🇮🇶": "العراق", "🇲🇦": "المغرب",
            "🇹🇳": "تونس", "🇯🇴": "الأردن", "🇺🇸": "أمريكا", "🇪🇸": "إسبانيا",
            "🇹🇷": "تركيا", "🇰🇷": "كوريا الجنوبية", "🇯🇵": "اليابان", "🇩🇪": "ألمانيا",
            "🇫🇷": "فرنسا", "🇬🇧": "المملكة المتحدة", "🇷🇺": "روسيا", "🇨🇳": "الصين",
            "🌐": "دولة أخرى"
        }
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
        "not_set": "Not Set",
        "countries": {
            "🇾🇪": "Yemen", "🇸🇦": "Saudi Arabia", "🇪🇬": "Egypt", "🇩🇿": "Algeria",
            "🇵🇸": "Palestine", "🇦🇪": "UAE", "🇮🇶": "Iraq", "🇲🇦": "Morocco",
            "🇹🇳": "Tunisia", "🇯🇴": "Jordan", "🇺🇸": "USA", "🇪🇸": "Spain",
            "🇹🇷": "Turkey", "🇰🇷": "South Korea", "🇯🇵": "Japan", "🇩🇪": "Germany",
            "🇫🇷": "France", "🇬🇧": "United Kingdom", "🇷🇺": "Russia", "🇨🇳": "China",
            "🌐": "Other Country"
        }
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
        "not_set": "未設定",
        "countries": {
            "🇾🇪": "イエメン", "🇸🇦": "サウジアラビア", "🇪🇬": "エジプト", "🇩🇿": "アルジェリア",
            "🇵🇸": "パレスチナ", "🇦🇪": "アラブ首長国連邦", "🇮🇶": "イラク", "🇲🇦": "モロッコ",
            "🇹🇳": "チュニジア", "🇯🇴": "ヨルダン", "🇺🇸": "アメリカ", "🇪🇸": "スペイン",
            "🇹🇷": "トルコ", "🇰🇷": "韓国", "🇯🇵": "日本", "🇩🇪": "ドイツ",
            "🇫🇷": "フランス", "🇬🇧": "イギリス", "🇷🇺": "ロシア", "🇨🇳": "中国",
            "🌐": "その他の国"
        }
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
        "not_set": "No establecido",
        "countries": {
            "🇾🇪": "Yemen", "🇸🇦": "Arabia Saudita", "🇪🇬": "Egipto", "🇩🇿": "Argelia",
            "🇵🇸": "Palestina", "🇦🇪": "EAU", "🇮🇶": "Irak", "🇲🇦": "Marruecos",
            "🇹🇳": "Túnez", "🇯🇴": "Jordania", "🇺🇸": "EE. UU.", "🇪🇸": "España",
            "🇹🇷": "Turquía", "🇰🇷": "Corea del Sur", "🇯🇵": "Japón", "🇩🇪": "Alemania",
            "🇫🇷": "Francia", "🇬🇧": "Reino Unido", "🇷🇺": "Rusia", "🇨🇳": "China",
            "🌐": "Otro País"
        }
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
        "not_set": "설정되지 않음",
        "countries": {
            "🇾🇪": "예멘", "🇸🇦": "사우디아라비아", "🇪🇬": "이집트", "🇩🇿": "알제리",
            "🇵🇸": "팔레스타인", "🇦🇪": "아랍에미리트", "🇮🇶": "이라크", "🇲🇦": "모로코",
            "🇹🇳": "튀니지", "🇯🇴": "요르단", "🇺🇸": "미국", "🇪🇸": "스페인",
            "🇹🇷": "튀르키예", "🇰🇷": "대한민국", "🇯🇵": "일본", "🇩🇪": "독일",
            "🇫🇷": "프랑스", "🇬🇧": "영국", "🇷🇺": "러시아", "🇨🇳": "중국",
            "🌐": "기타 국가"
        }
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

COUNTRY_CODES = [
    "🇾🇪", "🇸🇦", "🇪🇬", "🇩🇿", "🇵🇸", "🇦🇪", "🇮🇶", "🇲🇦", "🇹🇳", "🇯🇴",
    "🇺🇸", "🇪🇸", "🇹🇷", "🇰🇷", "🇯🇵", "🇩🇪", "🇫🇷", "🇬🇧", "🇷🇺", "🇨🇳", "🌐"
]

COUNTRY_ROLES = COUNTRY_CODES

# --- القوائم المنسدلة الذكية مع دعم التحديد المسبق ---
class GenderSelect(discord.ui.Select):

    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        
        options = [
            discord.SelectOption(
                label=t["gender_m"], emoji="♂️", value="♂️", default=(current_val == "♂️")
            ),
            discord.SelectOption(
                label=t["gender_f"], emoji="♀️", value="♀️", default=(current_val == "♀️")
            ),
        ]
        super().__init__(
            placeholder=t["gender_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_gender = self.values[0]
        update_user_field(interaction.user.id, "gender", selected_gender)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = (
            discord.Color.blue()
            if selected_gender == "♂️"
            else discord.Color.pink()
        )

        await assign_profile_role(
            interaction, GENDER_ROLES, selected_gender, role_color
        )
        await interaction.response.send_message(
            t["saved_gender"], ephemeral=True
        )


class AgeSelect(discord.ui.Select):

    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        
        options = [
            discord.SelectOption(
                label=age, value=age, default=(current_val == age)
            ) for age in AGE_ROLES
        ]
        super().__init__(
            placeholder=t["age_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_age = self.values[0]
        update_user_field(interaction.user.id, "age", selected_age)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = discord.Color.from_rgb(155, 89, 182)

        await assign_profile_role(
            interaction, AGE_ROLES, selected_age, role_color
        )
        await interaction.response.send_message(t["saved_age"], ephemeral=True)


class CountrySelect(discord.ui.Select):

    def __init__(self, lang: str, current_val: str = None):
        self.lang = lang
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        country_dict = t.get("countries", TRANSLATIONS["en"]["countries"])

        options = [
            discord.SelectOption(
                label=country_dict.get(code, code),
                emoji=code,
                value=code,
                default=(current_val == code)
            )
            for code in COUNTRY_CODES
        ]
        super().__init__(
            placeholder=t["country_ph"],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_country = self.values[0]
        update_user_field(interaction.user.id, "country", selected_country)
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        role_color = discord.Color.from_rgb(46, 204, 113)

        await assign_profile_role(
            interaction, COUNTRY_ROLES, selected_country, role_color
        )
        await interaction.response.send_message(
            t["saved_country"], ephemeral=True
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


# --- واجهة أزرار اختيار اللغة الأساسية ---
class LanguageButtonView(discord.ui.View):

    def __init__(self, current_lang: str = None):
        super().__init__(timeout=None)
        
        # إذا تم تزويد اللغة الحالية، نقوم بتمييز الزر الخاص بها
        if current_lang:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.custom_id == f"btn_{current_lang}":
                        item.style = discord.ButtonStyle.success

    async def handle_lang_click(
        self, interaction: discord.Interaction, lang_code: str
    ):
        update_user_field(interaction.user.id, "language", lang_code)
        t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
        embed = discord.Embed(
            title=t["title"],
            description="Fill your profile options below:",
            color=discord.Color.green(),
        )
        user_data = get_user_profile(interaction.user.id)
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(lang_code, user_data), ephemeral=True
        )

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

    def __init__(self, user_lang: str, user_data: dict = None):
        super().__init__(timeout=None)
        self.user_lang = user_lang
        self.user_data = user_data or {}
        
        t = TRANSLATIONS.get(user_lang, TRANSLATIONS["en"])
        
        # لتحديث نصوص الأزرار لتطابق لغة البروفايل المحددة
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "btn_edit_profile":
                    item.label = t["edit_btn"]
                elif item.custom_id == "btn_change_lang":
                    item.label = t["change_lang_btn"]

    @discord.ui.button(
        label="Edit Profile",
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
        user_data = get_user_profile(interaction.user.id)
        await interaction.response.send_message(
            embed=embed, view=DetailsSurveyView(self.user_lang, user_data), ephemeral=True
        )

    @discord.ui.button(
        label="Change Language",
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
            embed=embed, view=LanguageButtonView(current_lang=self.user_lang), ephemeral=True
        )


# --- الأحداث والبداية ---
@bot.event
async def on_ready():
    try:
        await bot.load_extension("games")
    except Exception as e:
        print(f"⚠️ Extension load status: {e}")

    bot.add_view(LanguageButtonView())
    synced = await bot.tree.sync()
    print(
        f"تم تسجيل الدخول باسم {bot.user}، وتم مزامنة الأوامر بنجاح!"
    )


# إرسال الاستبيان واللغة تلقائياً في الخاص فور انضمام عضو جديد
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
        print(f"لم نتمكن من إرسال رسالة خاصة للعضو {member.name}")


# --- أمر عرض وتعديل البروفايل ---
@bot.tree.command(
    name="profile", description="عرض وتعديل بيانات ملفك الشخصي ولغتك المفضلة"
)
async def view_profile(interaction: discord.Interaction):
    user_data = get_user_profile(interaction.user.id)

    lang = user_data.get("language", "en")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    country_code = user_data.get("country", "Not Set")
    country_dict = t.get("countries", TRANSLATIONS["en"]["countries"])
    display_country = country_dict.get(country_code, country_code if country_code != "Not Set" else t["not_set"])

    gender_val = user_data.get("gender", "Not Set")
    if gender_val == "♂️":
        display_gender = t["gender_m"]
    elif gender_val == "♀️":
        display_gender = t["gender_f"]
    else:
        display_gender = t["not_set"]

    age_val = user_data.get("age", t["not_set"])
    if age_val == "Not Set":
        age_val = t["not_set"]

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
        value=display_gender,
        inline=True,
    )
    embed.add_field(
        name=f"🎂 {t['age_label']}",
        value=age_val,
        inline=True,
    )
    embed.add_field(
        name=f"🚩 {t['country_label']}",
        value=display_country,
        inline=True,
    )

    await interaction.response.send_message(
        embed=embed, view=ProfileManageView(lang, user_data), ephemeral=True
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
        user_info = get_user_profile(interaction.user.id)
        final_lang = user_info.get("language", "en")

    try:
        translated_text = translate_smart_preserve_format(
            target_msg.content, final_lang
        )
        response_text = f"🌐 **الترجمة إلى ({final_lang}):**\n\n{translated_text}"
        await interaction.followup.send(response_text, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            f"❌ حدث خطأ أثناء الترجمة: {e}", ephemeral=True
        )


# =========================================================
# أمر ترجمة العربيزي (/arabizi) - يعمل بالرد فقط (Reply)
# =========================================================
@bot.tree.command(
    name="arabizi", description="ترجمة رسالة عربيزي قمت بالرد عليها (Reply)"
)
async def translate_arabizi_cmd(interaction: discord.Interaction):
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
                target_msg = await channel.fetch_message(msg.reference.message_id)
                break
    except Exception:
        pass

    if not target_msg or not target_msg.content:
        await interaction.response.send_message(
            "⚠️ يرجى استخدام الأمر `/arabizi` كـ **رد (Reply)** على الرسالة التي تريد ترجمتها!",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    arabic_text = process_arabizi_text(target_msg.content)

    user_info = get_user_profile(interaction.user.id)
    user_lang = user_info.get("language", "ar")

    if user_lang != "ar":
        final_output = translate_smart_preserve_format(arabic_text, user_lang)
        response_msg = f"🔤 **الترجمة من العربيزي ({user_lang}):**\n\n{final_output}"
    else:
        response_msg = f"🔤 **الترجمة من العربيزي:**\n\n{arabic_text}"

    await interaction.followup.send(response_msg, ephemeral=True)


# --- أمر الترجمة بالزر الأيمن للفأرة (Context Menu) ---
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
    user_info = get_user_profile(interaction.user.id)
    target_lang = user_info.get("language", "en")

    try:
        translated_text = translate_smart_preserve_format(
            message.content, target_lang
        )
        response_text = f"🌐 **الترجمة إلى ({target_lang}):**\n\n{translated_text}"
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