import json
import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands


# =========================================================
# الإعدادات
# =========================================================

GAMES_CHANNEL_ID = 1537949579457339483
GAMES_CHANNEL_URL = "https://discord.com/channels/1529585792194707609/1537949579457339483"
DATA_FILE = "user_profiles.json"
ALLOWED_GAME_COMMANDS = {"xo", "rps", "connect4", "games"}


# =========================================================
# جلب لغة المستخدم (اللغة الافتراضية: الإنجليزية)
# =========================================================

def get_user_lang(user_id: int) -> str:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            lang = data.get(str(user_id), {}).get("language", "en")

            if lang in ("ar", "en", "es", "ja", "ko"):
                return lang

        except Exception:
            pass

    return "en"


# =========================================================
# النصوص
# =========================================================

TEXTS = {
    "en": {
        "xo_title": "Tic-Tac-Toe",
        "rps_title": "Rock Paper Scissors",
        "c4_title": "Connect Four",
        "winner": "Winner",
        "loser": "Loser",
        "draw": "Draw",
    },
    "ar": {
        "xo_title": "إكس أوه",
        "rps_title": "حجرة ورقة مقص",
        "c4_title": "أربع تربح",
        "winner": "الفائز",
        "loser": "الخاسر",
        "draw": "تعادل",
    },
    "es": {
        "xo_title": "Tres en Raya",
        "rps_title": "Piedra Papel Tijeras",
        "c4_title": "Conecta Cuatro",
        "winner": "Ganador",
        "loser": "Perdedor",
        "draw": "Empate",
    },
    "ja": {
        "xo_title": "○×ゲーム",
        "rps_title": "じゃんけん",
        "c4_title": "コネクトフォー",
        "winner": "勝者",
        "loser": "敗者",
        "draw": "引き分け",
    },
    "ko": {
        "xo_title": "틱택토",
        "rps_title": "가위바위보",
        "c4_title": "커넥트 포",
        "winner": "승자",
        "loser": "패자",
        "draw": "무승부",
    },
}


def get_bi_text(p1_id: int, p2_id: int, key: str) -> str:
    lang1 = get_user_lang(p1_id)
    lang2 = get_user_lang(p2_id)

    text1 = TEXTS.get(lang1, TEXTS["en"]).get(key, "")
    text2 = TEXTS.get(lang2, TEXTS["en"]).get(key, "")

    if lang1 == lang2:
        return text1

    return f"{text1} / {text2}"


# =========================================================
# واجهة التحويل إلى قناة الألعاب
# =========================================================

class GoToGamesChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="🧩 الانتقال إلى روم الألعاب / Go to Games",
                url=GAMES_CHANNEL_URL,
                style=discord.ButtonStyle.link,
            )
        )


async def check_games_channel(interaction: discord.Interaction) -> bool:
    """تحقق مما إذا كان المستخدم داخل روم الألعاب أم لا"""
    if interaction.channel_id != GAMES_CHANNEL_ID:
        await interaction.response.send_message(
            "⚠️ **عذراً، هذه الأوامر مخصصة فقط لقناة الألعاب!**\n"
            "Sorry, these commands can only be used in the games channel!",
            view=GoToGamesChannelView(),
            ephemeral=True,
        )
        return False
    return True


# =========================================================
# 1. TIC-TAC-TOE
# =========================================================

class TicTacToeButton(discord.ui.Button):

    def __init__(self, x: int, y: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="\u200b",
            row=y
        )
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view

        if interaction.user not in (view.player1, view.player2):
            await interaction.response.defer()
            return

        if interaction.user != view.current_player:
            await interaction.response.defer()
            return

        if view.board[self.y][self.x] != 0:
            await interaction.response.defer()
            return

        await view.process_turn(interaction, self)


class TicTacToeView(discord.ui.View):

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        b = self.board
        lines = (
            b[0], b[1], b[2],
            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]],
        )

        for line in lines:
            if line[0] == line[1] == line[2] != 0:
                return self.player1 if line[0] == 1 else self.player2

        return None

    def is_full(self):
        return all(cell != 0 for row in self.board for cell in row)

    async def process_turn(self, interaction: discord.Interaction, button: TicTacToeButton):
        if self.current_player == self.player1:
            button.label = "❌"
            button.style = discord.ButtonStyle.danger
            self.board[button.y][button.x] = 1
            next_player = self.player2
        else:
            button.label = "⭕"
            button.style = discord.ButtonStyle.primary
            self.board[button.y][button.x] = 2
            next_player = self.player1

        button.disabled = True
        title = get_bi_text(self.player1.id, self.player2.id, "xo_title")
        winner = self.check_winner()

        if winner:
            for child in self.children:
                child.disabled = True

            loser = self.player2 if winner == self.player1 else self.player1
            winner_label = get_bi_text(self.player1.id, self.player2.id, "winner")
            loser_label = get_bi_text(self.player1.id, self.player2.id, "loser")
            winner_symbol = "❌" if winner == self.player1 else "⭕"
            loser_symbol = "❌" if loser == self.player1 else "⭕"

            content = (
                f"{title}\n\n"
                f"{winner_label}\n"
                f"{winner_symbol} {winner.mention}\n\n"
                f"{loser_label}\n"
                f"{loser_symbol} {loser.mention}"
            )

            if interaction.response.is_done():
                await interaction.message.edit(content=content, view=self)
            else:
                await interaction.response.edit_message(content=content, view=self)
            self.stop()
            return

        if self.is_full():
            for child in self.children:
                child.disabled = True

            draw_label = get_bi_text(self.player1.id, self.player2.id, "draw")
            content = (
                f"{title}\n\n"
                f"{draw_label}\n\n"
                f"❌ {self.player1.mention} = ⭕ {self.player2.mention}"
            )

            if interaction.response.is_done():
                await interaction.message.edit(content=content, view=self)
            else:
                await interaction.response.edit_message(content=content, view=self)
            self.stop()
            return

        self.current_player = next_player
        current_symbol = "❌" if self.current_player == self.player1 else "⭕"

        content = (
            f"{title}\n\n"
            f"❌ {self.player1.mention} VS ⭕ {self.player2.mention}\n"
            f"👉 {current_symbol} {self.current_player.mention}"
        )

        if interaction.response.is_done():
            await interaction.message.edit(content=content, view=self)
        else:
            await interaction.response.edit_message(content=content, view=self)

        # إذا كان الدور على البوت، يلعب عشوائياً
        if self.current_player.bot:
            await asyncio.sleep(1)
            available_buttons = [b for b in self.children if isinstance(b, TicTacToeButton) and not b.disabled]
            if available_buttons:
                chosen_button = random.choice(available_buttons)
                await self.process_turn(interaction, chosen_button)


# =========================================================
# 2. ROCK PAPER SCISSORS
# =========================================================

class RPSView(discord.ui.View):

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=120)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}

        # اختيار عشوائي للبوت مسبقاً إذا كان مشاركاً
        if self.player2.bot:
            self.choices[self.player2.id] = random.choice(["rock", "paper", "scissors"])

    @discord.ui.button(label="🪨", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "rock")

    @discord.ui.button(label="📄", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "paper")

    @discord.ui.button(label="✂️", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "scissors")

    async def make_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user not in (self.player1, self.player2):
            await interaction.response.defer()
            return

        if interaction.user.id in self.choices:
            await interaction.response.defer()
            return

        self.choices[interaction.user.id] = choice
        await interaction.response.defer()

        if len(self.choices) < 2:
            return

        c1 = self.choices[self.player1.id]
        c2 = self.choices[self.player2.id]
        emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        for child in self.children:
            child.disabled = True

        title = get_bi_text(self.player1.id, self.player2.id, "rps_title")

        if c1 == c2:
            draw_label = get_bi_text(self.player1.id, self.player2.id, "draw")
            content = (
                f"{title}\n\n"
                f"{self.player1.mention} {emoji_map[c1]} VS {self.player2.mention} {emoji_map[c2]}\n\n"
                f"{draw_label}\n\n"
                f"{self.player1.mention} {emoji_map[c1]} = {self.player2.mention} {emoji_map[c2]}"
            )
            await interaction.message.edit(content=content, view=self)
            self.stop()
            return

        player1_wins = (
            (c1 == "rock" and c2 == "scissors") or
            (c1 == "paper" and c2 == "rock") or
            (c1 == "scissors" and c2 == "paper")
        )

        if player1_wins:
            winner, loser = self.player1, self.player2
            winner_choice, loser_choice = c1, c2
        else:
            winner, loser = self.player2, self.player1
            winner_choice, loser_choice = c2, c1

        winner_label = get_bi_text(self.player1.id, self.player2.id, "winner")
        loser_label = get_bi_text(self.player1.id, self.player2.id, "loser")

        content = (
            f"{title}\n\n"
            f"{self.player1.mention} {emoji_map[c1]} VS {self.player2.mention} {emoji_map[c2]}\n\n"
            f"{winner_label}\n"
            f"{emoji_map[winner_choice]} {winner.mention}\n\n"
            f"{loser_label}\n"
            f"{emoji_map[loser_choice]} {loser.mention}"
        )

        await interaction.message.edit(content=content, view=self)
        self.stop()


# =========================================================
# 3. CONNECT FOUR
# =========================================================

class ConnectFourView(discord.ui.View):

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0] * 7 for _ in range(6)]

        for col in range(7):
            self.add_item(self.ColButton(col))

    class ColButton(discord.ui.Button):

        def __init__(self, col: int):
            super().__init__(
                label=str(col + 1),
                style=discord.ButtonStyle.primary,
                row=0 if col < 4 else 1
            )
            self.col = col

        async def callback(self, interaction: discord.Interaction):
            view: ConnectFourView = self.view

            if interaction.user not in (view.player1, view.player2):
                await interaction.response.defer()
                return

            if interaction.user != view.current_player:
                await interaction.response.defer()
                return

            await view.process_turn(interaction, self.col)

    async def process_turn(self, interaction: discord.Interaction, col: int):
        row_to_place = -1
        for r in range(5, -1, -1):
            if self.board[r][col] == 0:
                row_to_place = r
                break

        if row_to_place == -1:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

        piece = 1 if self.current_player == self.player1 else 2
        self.board[row_to_place][col] = piece

        title = get_bi_text(self.player1.id, self.player2.id, "c4_title")

        if self.check_win(piece):
            for child in self.children:
                child.disabled = True

            winner = self.current_player
            loser = self.player2 if winner == self.player1 else self.player1
            winner_label = get_bi_text(self.player1.id, self.player2.id, "winner")
            loser_label = get_bi_text(self.player1.id, self.player2.id, "loser")
            winner_symbol = "🔴" if winner == self.player1 else "🟡"
            loser_symbol = "🔴" if loser == self.player1 else "🟡"

            msg = (
                f"{self.render_board()}\n\n"
                f"{title}\n\n"
                f"{winner_label}\n"
                f"{winner_symbol} {winner.mention}\n\n"
                f"{loser_label}\n"
                f"{loser_symbol} {loser.mention}"
            )

            if interaction.response.is_done():
                await interaction.message.edit(content=msg, view=self)
            else:
                await interaction.response.edit_message(content=msg, view=self)
            self.stop()
            return

        # تعطيل أزرار الأعمدة الممتلئة بالكامل (7 خيارات تقل عند امتلاء العمود)
        for child in self.children:
            if isinstance(child, self.ColButton):
                if self.board[0][child.col] != 0:
                    child.disabled = True

        if all(self.board[0][c] != 0 for c in range(7)):
            for child in self.children:
                child.disabled = True

            draw_label = get_bi_text(self.player1.id, self.player2.id, "draw")
            msg = (
                f"{self.render_board()}\n\n"
                f"{title}\n\n"
                f"{draw_label}\n\n"
                f"🔴 {self.player1.mention} = 🟡 {self.player2.mention}"
            )

            if interaction.response.is_done():
                await interaction.message.edit(content=msg, view=self)
            else:
                await interaction.response.edit_message(content=msg, view=self)
            self.stop()
            return

        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        current_symbol = "🔴" if self.current_player == self.player1 else "🟡"

        msg = (
            f"{self.render_board()}\n\n"
            f"{title}\n\n"
            f"🔴 {self.player1.mention} VS 🟡 {self.player2.mention}\n"
            f"👉 {current_symbol} {self.current_player.mention}"
        )

        if interaction.response.is_done():
            await interaction.message.edit(content=msg, view=self)
        else:
            await interaction.response.edit_message(content=msg, view=self)

        # إذا كان الدور على البوت، يختار عموداً متاحاً عشوائياً
        if self.current_player.bot:
            await asyncio.sleep(1)
            valid_cols = [c for c in range(7) if self.board[0][c] == 0]
            if valid_cols:
                chosen_col = random.choice(valid_cols)
                await self.process_turn(interaction, chosen_col)

    def render_board(self) -> str:
        symbols = {0: "⚪", 1: "🔴", 2: "🟡"}
        result = ""
        for row in self.board:
            result += "".join(symbols[cell] for cell in row) + "\n"
        result += "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        return result

    def check_win(self, player: int) -> bool:
        for r in range(6):
            for c in range(7):
                if c + 3 < 7 and all(self.board[r][c + i] == player for i in range(4)):
                    return True
                if r + 3 < 6 and all(self.board[r + i][c] == player for i in range(4)):
                    return True
                if r + 3 < 6 and c + 3 < 7 and all(self.board[r + i][c + i] == player for i in range(4)):
                    return True
                if r - 3 >= 0 and c + 3 < 7 and all(self.board[r - i][c + i] == player for i in range(4)):
                    return True
        return False


# =========================================================
# GAMES COG
# =========================================================

class GamesCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == GAMES_CHANNEL_ID:
            if message.author.id != self.bot.user.id:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

    @app_commands.command(
        name="games",
        description="Show available server games and instructions / عرض قائمة الألعاب والشرح"
    )
    async def games_menu(self, interaction: discord.Interaction):
        if not await check_games_channel(interaction):
            return

        embed = discord.Embed(
            title="🎮 قائمة ألعاب السيرفر / Server Games",
            description="مرحباً بك في قسم الألعاب! يمكنك منافسة الأعضاء باستخدام الأوامر التالية:",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="❌⭕ 1. لعبة إكس أوه (/xo)",
            value=(
                "**الاستخدام:** `/xo @User`\n"
                "**الشرح:** لعبة Tic-Tac-Toe المعروفة. تناوب مع خصمك على إكمال خط من 3 رمور (أفقياً، عمودياً، أو قطرياً) لتمكين الفوز."
            ),
            inline=False
        )

        embed.add_field(
            name="🪨📄✂️ 2. حجرة ورقة مقص (/rps)",
            value=(
                "**الاستخدام:** `/rps @User`\n"
                "**الشرح:** اخترا خياراتكما سرا بالضغط على الأزرار. الحجرة تهزم المقص، والمقص يهزم الورقة، والورقة تهزم الحجرة."
            ),
            inline=False
        )

        embed.add_field(
            name="🔴🟡 3. لعبة أربع تربح (/connect4)",
            value=(
                "**الاستخدام:** `/connect4 @User`\n"
                "**الشرح:** اختر العمود (1-7) لإسقاط القرص الخاص بك. أول لاعب يجمع 4 أقراص متتالية في أي اتجاه يفوز."
            ),
            inline=False
        )

        embed.set_footer(text="ملاحظة: جميع الأوامر تعمل حصرياً في هذه القناة.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="xo",
        description="Start a Tic-Tac-Toe game / بدء لعبة إكس أوه"
    )
    async def xo(self, interaction: discord.Interaction, opponent: discord.User):
        if not await check_games_channel(interaction):
            return

        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ لا يمكنك اللعب ضد نفسك!", ephemeral=True
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        title = get_bi_text(interaction.user.id, opponent.id, "xo_title")

        msg = (
            f"{title}\n\n"
            f"❌ {interaction.user.mention} VS ⭕ {opponent.mention}\n"
            f"👉 ❌ {interaction.user.mention}"
        )

        await interaction.response.send_message(msg, view=view)

    @app_commands.command(
        name="rps",
        description="Start Rock Paper Scissors / بدء لعبة حجرة ورقة مقص"
    )
    async def rps(self, interaction: discord.Interaction, opponent: discord.User):
        if not await check_games_channel(interaction):
            return

        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ لا يمكنك اللعب ضد نفسك!", ephemeral=True
            )
            return

        view = RPSView(interaction.user, opponent)
        title = get_bi_text(interaction.user.id, opponent.id, "rps_title")

        msg = (
            f"{title}\n\n"
            f"{interaction.user.mention} VS {opponent.mention}"
        )

        await interaction.response.send_message(msg, view=view)

    @app_commands.command(
        name="connect4",
        description="Start a Connect Four game / بدء لعبة أربع تربح"
    )
    async def connect4(self, interaction: discord.Interaction, opponent: discord.User):
        if not await check_games_channel(interaction):
            return

        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ لا يمكنك اللعب ضد نفسك!", ephemeral=True
            )
            return

        view = ConnectFourView(interaction.user, opponent)
        title = get_bi_text(interaction.user.id, opponent.id, "c4_title")

        msg = (
            f"{view.render_board()}\n\n"
            f"{title}\n\n"
            f"🔴 {interaction.user.mention} VS 🟡 {opponent.mention}\n"
            f"👉 🔴 {interaction.user.mention}"
        )

        await interaction.response.send_message(msg, view=view)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    cog = GamesCog(bot)

    async def global_interaction_check(interaction: discord.Interaction) -> bool:
        if interaction.channel_id == GAMES_CHANNEL_ID:
            cmd_name = interaction.command.name if interaction.command else None
            if cmd_name not in ALLOWED_GAME_COMMANDS:
                if not interaction.response.is_done():
                    await interaction.response.defer()
                return False
        return True

    bot.check_once(global_interaction_check)
    await bot.add_cog(cog)