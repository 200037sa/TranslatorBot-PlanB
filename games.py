import json
import os
import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# الإعدادات
# ============================================================

GAMES_CHANNEL_ID = 1537829034065403925
DATA_FILE = "user_profiles.json"


# ============================================================
# جلب لغة المستخدم
# ============================================================

def get_user_lang(user_id: int) -> str:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            lang = data.get(str(user_id), {}).get("language", "ar")

            if lang in TEXTS:
                return lang

        except Exception:
            pass

    return "ar"


# ============================================================
# النصوص
# ============================================================

TEXTS = {
    "ar": {
        "xo_title": "إكس أوه",
        "rps_title": "حجرة ورقة مقص",
        "c4_title": "أربع تربح",

        "turn": "الدور",

        "winner": "الفائز",
        "loser": "الخاسر",
        "draw": "تعادل",
    },

    "en": {
        "xo_title": "Tic-Tac-Toe",
        "rps_title": "Rock Paper Scissors",
        "c4_title": "Connect Four",

        "turn": "Turn",

        "winner": "Winner",
        "loser": "Loser",
        "draw": "Draw",
    },

    "es": {
        "xo_title": "Tres en Raya",
        "rps_title": "Piedra Papel Tijeras",
        "c4_title": "Conecta Cuatro",

        "turn": "Turno",

        "winner": "Ganador",
        "loser": "Perdedor",
        "draw": "Empate",
    },

    "ja": {
        "xo_title": "○×ゲーム",
        "rps_title": "じゃんけん",
        "c4_title": "コネクトフォー",

        "turn": "手番",

        "winner": "勝者",
        "loser": "敗者",
        "draw": "引き分け",
    },

    "ko": {
        "xo_title": "틱택토",
        "rps_title": "가위바위보",
        "c4_title": "커넥트 포",

        "turn": "차례",

        "winner": "승자",
        "loser": "패자",
        "draw": "무승부",
    },
}


# ============================================================
# نص ثنائي اللغة
#
# اللغة الأولى = اللاعب الأول
# اللغة الثانية = اللاعب الثاني
# ============================================================

def get_bi_text(p1_id: int, p2_id: int, key: str) -> str:
    lang1 = get_user_lang(p1_id)
    lang2 = get_user_lang(p2_id)

    t1 = TEXTS.get(lang1, TEXTS["ar"]).get(key, "")
    t2 = TEXTS.get(lang2, TEXTS["ar"]).get(key, "")

    if lang1 == lang2:
        return t1

    return f"{t1} / {t2}"


# ============================================================
# الرد الصامت على التفاعل غير المسموح
#
# لا تظهر رسالة للمستخدم.
# ============================================================

async def silent_response(interaction: discord.Interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except Exception:
        pass


# ============================================================
# 1. Tic-Tac-Toe
# ============================================================

class TicTacToeButton(discord.ui.Button):

    def __init__(self, x: int, y: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="\u200b",
            row=y,
        )

        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):

        view: TicTacToeView = self.view

        # ----------------------------------------------------
        # اللاعب ليس أحد لاعبي اللعبة
        # ----------------------------------------------------

        if interaction.user.id not in (
            view.player1.id,
            view.player2.id,
        ):
            await silent_response(interaction)
            return

        # ----------------------------------------------------
        # ليس دوره
        # ----------------------------------------------------

        if interaction.user.id != view.current_player.id:
            await silent_response(interaction)
            return

        # ----------------------------------------------------
        # الخانة مستخدمة
        # ----------------------------------------------------

        if view.board[self.y][self.x] != 0:
            await silent_response(interaction)
            return

        # ----------------------------------------------------
        # تسجيل الحركة
        # ----------------------------------------------------

        if view.current_player.id == view.player1.id:

            self.label = "❌"
            self.style = discord.ButtonStyle.danger

            view.board[self.y][self.x] = 1

            next_player = view.player2

        else:

            self.label = "⭕"
            self.style = discord.ButtonStyle.primary

            view.board[self.y][self.x] = 2

            next_player = view.player1

        self.disabled = True

        # ----------------------------------------------------
        # فحص الفوز
        # ----------------------------------------------------

        winner = view.check_winner()

        title = get_bi_text(
            view.player1.id,
            view.player2.id,
            "xo_title",
        )

        players_line = (
            f"❌ {view.player1.mention} VS "
            f"⭕ {view.player2.mention}"
        )

        # ----------------------------------------------------
        # فوز
        # ----------------------------------------------------

        if winner:

            for child in view.children:
                child.disabled = True

            loser = (
                view.player2
                if winner.id == view.player1.id
                else view.player1
            )

            winner_label = get_bi_text(
                view.player1.id,
                view.player2.id,
                "winner",
            )

            loser_label = get_bi_text(
                view.player1.id,
                view.player2.id,
                "loser",
            )

            content = (
                f"**{title}**\n"
                f"{players_line}\n\n"
                f"🏆 **{winner_label}:** {winner.mention}\n"
                f"💔 **{loser_label}:** {loser.mention}"
            )

            await interaction.response.edit_message(
                content=content,
                view=view,
            )

            view.stop()
            return

        # ----------------------------------------------------
        # تعادل
        # ----------------------------------------------------

        if view.is_full():

            for child in view.children:
                child.disabled = True

            draw_label = get_bi_text(
                view.player1.id,
                view.player2.id,
                "draw",
            )

            content = (
                f"**{title}**\n"
                f"{players_line}\n\n"
                f"🤝 **{draw_label}**\n"
                f"{players_line}"
            )

            await interaction.response.edit_message(
                content=content,
                view=view,
            )

            view.stop()
            return

        # ----------------------------------------------------
        # استمرار اللعبة
        # ----------------------------------------------------

        view.current_player = next_player

        turn_label = get_bi_text(
            view.player1.id,
            view.player2.id,
            "turn",
        )

        turn_symbol = (
            "❌"
            if view.current_player.id == view.player1.id
            else "⭕"
        )

        content = (
            f"**{title}**\n"
            f"{players_line}\n"
            f"👈 **{turn_label}:** "
            f"{turn_symbol} {view.current_player.mention}"
        )

        await interaction.response.edit_message(
            content=content,
            view=view,
        )


class TicTacToeView(discord.ui.View):

    def __init__(
        self,
        player1: discord.User,
        player2: discord.User,
    ):
        super().__init__(timeout=180)

        self.player1 = player1
        self.player2 = player2

        self.current_player = player1

        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for y in range(3):
            for x in range(3):
                self.add_item(
                    TicTacToeButton(x, y)
                )

    def check_winner(self):

        b = self.board

        lines = (
            b[0],
            b[1],
            b[2],

            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],

            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]],
        )

        for line in lines:

            if line[0] == line[1] == line[2] != 0:

                return (
                    self.player1
                    if line[0] == 1
                    else self.player2
                )

        return None

    def is_full(self):
        return all(
            cell != 0
            for row in self.board
            for cell in row
        )


# ============================================================
# 2. Rock Paper Scissors
#
# لا يوجد دور.
#
# اللاعب الأول والثاني يستطيعان الاختيار في أي وقت.
# النتيجة لا تظهر إلا بعد اختيار الاثنين.
# ============================================================

class RPSView(discord.ui.View):

    def __init__(
        self,
        player1: discord.User,
        player2: discord.User,
    ):
        super().__init__(timeout=120)

        self.player1 = player1
        self.player2 = player2

        self.choices = {}

    # --------------------------------------------------------
    # Rock
    # --------------------------------------------------------

    @discord.ui.button(
        label="🪨",
        style=discord.ButtonStyle.primary,
    )
    async def rock(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.make_choice(
            interaction,
            "rock",
        )

    # --------------------------------------------------------
    # Paper
    # --------------------------------------------------------

    @discord.ui.button(
        label="📄",
        style=discord.ButtonStyle.primary,
    )
    async def paper(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.make_choice(
            interaction,
            "paper",
        )

    # --------------------------------------------------------
    # Scissors
    # --------------------------------------------------------

    @discord.ui.button(
        label="✂️",
        style=discord.ButtonStyle.primary,
    )
    async def scissors(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.make_choice(
            interaction,
            "scissors",
        )

    # --------------------------------------------------------
    # تسجيل الاختيار
    # --------------------------------------------------------

    async def make_choice(
        self,
        interaction: discord.Interaction,
        choice: str,
    ):

        # ----------------------------------------------------
        # التأكد من أن المستخدم لاعب
        # ----------------------------------------------------

        if interaction.user.id not in (
            self.player1.id,
            self.player2.id,
        ):
            await silent_response(interaction)
            return

        # ----------------------------------------------------
        # تسجيل اختيار اللاعب
        # ----------------------------------------------------

        self.choices[interaction.user.id] = choice

        # ----------------------------------------------------
        # اللاعب اختار، لكن اللاعب الثاني لم يختر بعد
        #
        # لا نغير الرسالة العامة.
        # لا نرسل أي رسالة.
        # ----------------------------------------------------

        if len(self.choices) < 2:

            await interaction.response.defer(
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # اللاعبان اختارا
        # ----------------------------------------------------

        c1 = self.choices[self.player1.id]
        c2 = self.choices[self.player2.id]

        emoji_map = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️",
        }

        for child in self.children:
            child.disabled = True

        title = get_bi_text(
            self.player1.id,
            self.player2.id,
            "rps_title",
        )

        players_line = (
            f"{self.player1.mention} ({emoji_map[c1]}) "
            f"VS "
            f"{self.player2.mention} ({emoji_map[c2]})"
        )

        # ----------------------------------------------------
        # تعادل
        # ----------------------------------------------------

        if c1 == c2:

            draw_label = get_bi_text(
                self.player1.id,
                self.player2.id,
                "draw",
            )

            content = (
                f"**{title}**\n"
                f"{players_line}\n\n"
                f"🤝 **{draw_label}**\n"
                f"{self.player1.mention} ({emoji_map[c1]}) = "
                f"{self.player2.mention} ({emoji_map[c2]})"
            )

            await interaction.response.edit_message(
                content=content,
                view=self,
            )

            self.stop()
            return

        # ----------------------------------------------------
        # تحديد الفائز
        # ----------------------------------------------------

        player1_wins = (
            (c1 == "rock" and c2 == "scissors")
            or
            (c1 == "paper" and c2 == "rock")
            or
            (c1 == "scissors" and c2 == "paper")
        )

        winner = (
            self.player1
            if player1_wins
            else self.player2
        )

        loser = (
            self.player2
            if winner.id == self.player1.id
            else self.player1
        )

        winner_label = get_bi_text(
            self.player1.id,
            self.player2.id,
            "winner",
        )

        loser_label = get_bi_text(
            self.player1.id,
            self.player2.id,
            "loser",
        )

        winner_choice = (
            emoji_map[c1]
            if winner.id == self.player1.id
            else emoji_map[c2]
        )

        loser_choice = (
            emoji_map[c2]
            if loser.id == self.player2.id
            else emoji_map[c1]
        )

        content = (
            f"**{title}**\n"
            f"{players_line}\n\n"
            f"🏆 **{winner_label}:** "
            f"{winner.mention} ({winner_choice})\n"
            f"💔 **{loser_label}:** "
            f"{loser.mention} ({loser_choice})"
        )

        await interaction.response.edit_message(
            content=content,
            view=self,
        )

        self.stop()


# ============================================================
# 3. Connect Four
# ============================================================

class ConnectFourView(discord.ui.View):

    def __init__(
        self,
        player1: discord.User,
        player2: discord.User,
    ):
        super().__init__(timeout=300)

        self.player1 = player1
        self.player2 = player2

        self.current_player = player1

        # 6 صفوف × 7 أعمدة
        self.board = [
            [0] * 7
            for _ in range(6)
        ]

        for col in range(7):
            self.add_item(
                self.ColButton(col)
            )

    # ========================================================
    # زر العمود
    # ========================================================

    class ColButton(discord.ui.Button):

        def __init__(self, col: int):

            super().__init__(
                label=str(col + 1),
                style=discord.ButtonStyle.primary,
                row=0 if col < 4 else 1,
            )

            self.col = col

        async def callback(
            self,
            interaction: discord.Interaction,
        ):

            view: ConnectFourView = self.view

            # ------------------------------------------------
            # ليس لاعباً
            # ------------------------------------------------

            if interaction.user.id not in (
                view.player1.id,
                view.player2.id,
            ):
                await silent_response(interaction)
                return

            # ------------------------------------------------
            # ليس دوره
            # ------------------------------------------------

            if interaction.user.id != view.current_player.id:
                await silent_response(interaction)
                return

            # ------------------------------------------------
            # إيجاد مكان القطعة
            # ------------------------------------------------

            row_to_place = -1

            for r in range(5, -1, -1):

                if view.board[r][self.col] == 0:
                    row_to_place = r
                    break

            # ------------------------------------------------
            # العمود ممتلئ
            # ------------------------------------------------

            if row_to_place == -1:
                await silent_response(interaction)
                return

            # ------------------------------------------------
            # وضع القطعة
            # ------------------------------------------------

            piece = (
                1
                if view.current_player.id == view.player1.id
                else 2
            )

            view.board[row_to_place][self.col] = piece

            title = get_bi_text(
                view.player1.id,
                view.player2.id,
                "c4_title",
            )

            players_line = (
                f"🔴 {view.player1.mention} VS "
                f"🟡 {view.player2.mention}"
            )

            # ------------------------------------------------
            # فوز
            # ------------------------------------------------

            if view.check_win(piece):

                for child in view.children:
                    child.disabled = True

                winner = view.current_player

                loser = (
                    view.player2
                    if winner.id == view.player1.id
                    else view.player1
                )

                winner_label = get_bi_text(
                    view.player1.id,
                    view.player2.id,
                    "winner",
                )

                loser_label = get_bi_text(
                    view.player1.id,
                    view.player2.id,
                    "loser",
                )

                winner_symbol = (
                    "🔴"
                    if winner.id == view.player1.id
                    else "🟡"
                )

                loser_symbol = (
                    "🟡"
                    if loser.id == view.player2.id
                    else "🔴"
                )

                msg = (
                    f"{view.render_board()}\n\n"
                    f"**{title}**\n"
                    f"{players_line}\n\n"
                    f"🏆 **{winner_label}:** "
                    f"{winner_symbol} {winner.mention}\n"
                    f"💔 **{loser_label}:** "
                    f"{loser_symbol} {loser.mention}"
                )

                await interaction.response.edit_message(
                    content=msg,
                    view=view,
                )

                view.stop()
                return

            # ------------------------------------------------
            # تعادل
            # ------------------------------------------------

            if all(
                view.board[0][c] != 0
                for c in range(7)
            ):

                for child in view.children:
                    child.disabled = True

                draw_label = get_bi_text(
                    view.player1.id,
                    view.player2.id,
                    "draw",
                )

                msg = (
                    f"{view.render_board()}\n\n"
                    f"**{title}**\n"
                    f"{players_line}\n\n"
                    f"🤝 **{draw_label}**\n"
                    f"{players_line}"
                )

                await interaction.response.edit_message(
                    content=msg,
                    view=view,
                )

                view.stop()
                return

            # ------------------------------------------------
            # الانتقال للاعب الثاني
            # ------------------------------------------------

            view.current_player = (
                view.player2
                if view.current_player.id == view.player1.id
                else view.player1
            )

            turn_label = get_bi_text(
                view.player1.id,
                view.player2.id,
                "turn",
            )

            turn_symbol = (
                "🔴"
                if view.current_player.id == view.player1.id
                else "🟡"
            )

            msg = (
                f"{view.render_board()}\n\n"
                f"**{title}**\n"
                f"{players_line}\n"
                f"👈 **{turn_label}:** "
                f"{turn_symbol} {view.current_player.mention}"
            )

            await interaction.response.edit_message(
                content=msg,
                view=view,
            )

    # ========================================================
    # رسم اللوحة
    # ========================================================

    def render_board(self) -> str:

        symbols = {
            0: "⚪",
            1: "🔴",
            2: "🟡",
        }

        rows = []

        for row in self.board:
            rows.append(
                "".join(
                    symbols[cell]
                    for cell in row
                )
            )

        rows.append(
            "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        )

        return "\n".join(rows)

    # ========================================================
    # فحص الفوز
    # ========================================================

    def check_win(self, p: int) -> bool:

        for r in range(6):

            for c in range(7):

                # أفقي
                if c + 3 < 7:

                    if all(
                        self.board[r][c + i] == p
                        for i in range(4)
                    ):
                        return True

                # عمودي
                if r + 3 < 6:

                    if all(
                        self.board[r + i][c] == p
                        for i in range(4)
                    ):
                        return True

                # قطري ↘
                if (
                    r + 3 < 6
                    and c + 3 < 7
                ):

                    if all(
                        self.board[r + i][c + i] == p
                        for i in range(4)
                    ):
                        return True

                # قطري ↗
                if (
                    r - 3 >= 0
                    and c + 3 < 7
                ):

                    if all(
                        self.board[r - i][c + i] == p
                        for i in range(4)
                    ):
                        return True

        return False


# ============================================================
# Games Cog
# ============================================================

class GamesCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ========================================================
    # XO
    # ========================================================

    @app_commands.command(
        name="xo",
        description="Start a Tic-Tac-Toe game / بدء لعبة إكس أوه",
    )
    async def xo(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
    ):

        if interaction.channel_id != GAMES_CHANNEL_ID:
            await interaction.response.defer(
                ephemeral=True
            )
            return

        if (
            opponent.bot
            or opponent.id == interaction.user.id
        ):
            await interaction.response.defer(
                ephemeral=True
            )
            return

        view = TicTacToeView(
            interaction.user,
            opponent,
        )

        title = get_bi_text(
            interaction.user.id,
            opponent.id,
            "xo_title",
        )

        turn_label = get_bi_text(
            interaction.user.id,
            opponent.id,
            "turn",
        )

        msg = (
            f"**{title}**\n"
            f"❌ {interaction.user.mention} VS "
            f"⭕ {opponent.mention}\n"
            f"👈 **{turn_label}:** "
            f"❌ {interaction.user.mention}"
        )

        await interaction.response.send_message(
            msg,
            view=view,
        )

    # ========================================================
    # RPS
    # ========================================================

    @app_commands.command(
        name="rps",
        description="Start Rock Paper Scissors / بدء لعبة حجرة ورقة مقص",
    )
    async def rps(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
    ):

        if interaction.channel_id != GAMES_CHANNEL_ID:
            await interaction.response.defer(
                ephemeral=True
            )
            return

        if (
            opponent.bot
            or opponent.id == interaction.user.id
        ):
            await interaction.response.defer(
                ephemeral=True
            )
            return

        view = RPSView(
            interaction.user,
            opponent,
        )

        title = get_bi_text(
            interaction.user.id,
            opponent.id,
            "rps_title",
        )

        # ----------------------------------------------------
        # لا يوجد "اختر حركتك"
        # ولا يوجد دور.
        # ----------------------------------------------------

        msg = (
            f"**{title}**\n"
            f"{interaction.user.mention} VS "
            f"{opponent.mention}"
        )

        await interaction.response.send_message(
            msg,
            view=view,
        )

    # ========================================================
    # Connect Four
    # ========================================================

    @app_commands.command(
        name="connect4",
        description="Start a Connect Four game / بدء لعبة أربع تربح",
    )
    async def connect4(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
    ):

        if interaction.channel_id != GAMES_CHANNEL_ID:
            await interaction.response.defer(
                ephemeral=True
            )
            return

        if (
            opponent.bot
            or opponent.id == interaction.user.id
        ):
            await interaction.response.defer(
                ephemeral=True
            )
            return

        view = ConnectFourView(
            interaction.user,
            opponent,
        )

        title = get_bi_text(
            interaction.user.id,
            opponent.id,
            "c4_title",
        )

        turn_label = get_bi_text(
            interaction.user.id,
            opponent.id,
            "turn",
        )

        msg = (
            f"{view.render_board()}\n\n"
            f"**{title}**\n"
            f"🔴 {interaction.user.mention} VS "
            f"🟡 {opponent.mention}\n"
            f"👈 **{turn_label}:** "
            f"🔴 {interaction.user.mention}"
        )

        await interaction.response.send_message(
            msg,
            view=view,
        )


# ============================================================
# Setup
# ============================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(
        GamesCog(bot)
    )