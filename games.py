import json
import os
import discord
from discord import app_commands
from discord.ext import commands

# ⚠️ ضع هنا آيدي قناة الألعاب الخاصة بالسيرفر
GAMES_CHANNEL_ID = 1537829034065403925  # استبدل هذا الرقم بـ ID قناة الألعاب لديك

DATA_FILE = "user_profiles.json"


# --- دالة جلب لغة المستخدم من ملف البيانات ---
def get_user_lang(user_id: int) -> str:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    return "en"


# --- نصوص الألعاب بجميع اللغات المدعومة ---
GAME_TRANSLATIONS = {
    "ar": {
        "not_your_turn": "⚠️ ليس دورك الآن!",
        "not_a_player": "⚠️ أنت لست جزءاً من هذه اللعبة!",
        "win": "🎉 فاز {winner}!",
        "draw": "🤝 تعادل!",
        "turn": "🎮 دورك الآن يا {player}",
        "rps_title": "✂️ حجرة ورقة مقص",
        "rps_wait": "في انتظار اختيار الطرفين...",
        "c4_full": "⚠️ هذه العمود مكتمل، اختر عموداً آخر!",
    },
    "en": {
        "not_your_turn": "⚠️ It's not your turn!",
        "not_a_player": "⚠️ You are not part of this game!",
        "win": "🎉 {winner} won!",
        "draw": "🤝 It's a draw!",
        "turn": "🎮 It's your turn {player}",
        "rps_title": "✂️ Rock Paper Scissors",
        "rps_wait": "Waiting for both players...",
        "c4_full": "⚠️ This column is full, pick another one!",
    },
    "es": {
        "not_your_turn": "⚠️ ¡No es tu turno!",
        "not_a_player": "⚠️ ¡No eres parte de este juego!",
        "win": "🎉 ¡{winner} ha ganado!",
        "draw": "🤝 ¡Empate!",
        "turn": "🎮 Es tu turno {player}",
        "rps_title": "✂️ Piedra Papel Tijeras",
        "rps_wait": "Esperando a ambos jugadores...",
        "c4_full": "⚠️ ¡Esta columna está llena, elige otra!",
    },
    "ja": {
        "not_your_turn": "⚠️ あなたの番ではありません！",
        "not_a_player": "⚠️ あなたはこのゲームに参加していません！",
        "win": "🎉 {winner} の勝利！",
        "draw": "🤝 引き分け！",
        "turn": "🎮 次は {player} さんの番です",
        "rps_title": "✂️ じゃんけん",
        "rps_wait": "両プレイヤーの選択を待っています...",
        "c4_full": "⚠️ この列はいっぱいです。別の列を選んでください！",
    },
    "ko": {
        "not_your_turn": "⚠️ 당신의 차례가 아닙니다!",
        "not_a_player": "⚠️ 이 게임의 참가자가 아닙니다!",
        "win": "🎉 {winner} 님의 승리!",
        "draw": "🤝 비겼습니다!",
        "turn": "🎮 {player} 님의 차례입니다",
        "rps_title": "✂️ 가위바위보",
        "rps_wait": "두 플레이어의 선택을 기다리는 중...",
        "c4_full": "⚠️ 이 열은 가득 찼습니다. 다른 열을 선택하세요!",
    },
}


def t_game(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return GAME_TRANSLATIONS.get(lang, GAME_TRANSLATIONS["en"]).get(key, "")


# ==========================================
# 1. لعبة Tic-Tac-Toe (X O)
# ==========================================
class TicTacToeButton(discord.ui.Button):

    def __init__(self, x: int, y: int):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="\u200b", row=y
        )
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view

        if interaction.user not in (view.player1, view.player2):
            msg = t_game(interaction.user.id, "not_a_player")
            await interaction.response.send_message(msg, ephemeral=True)
            return

        if interaction.user != view.current_player:
            msg = t_game(interaction.user.id, "not_your_turn")
            await interaction.response.send_message(msg, ephemeral=True)
            return

        if view.board[self.y][self.x] != 0:
            return

        if view.current_player == view.player1:
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

        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            msg = t_game(interaction.user.id, "win").format(
                winner=interaction.user.mention
            )
            await interaction.response.edit_message(content=msg, view=view)
            view.stop()
        elif view.is_full():
            for child in view.children:
                child.disabled = True
            msg = t_game(interaction.user.id, "draw")
            await interaction.response.edit_message(content=msg, view=view)
            view.stop()
        else:
            view.current_player = next_player
            msg = t_game(next_player.id, "turn").format(
                player=next_player.mention
            )
            await interaction.response.edit_message(content=msg, view=view)


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
                return self.current_player
        return None

    def is_full(self):
        return all(cell != 0 for row in self.board for cell in row)


# ==========================================
# 2. لعبة Rock Paper Scissors (حجرة ورقة مقص)
# ==========================================
class RPSView(discord.ui.View):

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=120)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}

    @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.primary)
    async def rock(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "rock")

    @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.primary)
    async def paper(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "paper")

    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.primary)
    async def scissors(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "scissors")

    async def make_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user not in (self.player1, self.player2):
            msg = t_game(interaction.user.id, "not_a_player")
            await interaction.response.send_message(msg, ephemeral=True)
            return

        self.choices[interaction.user.id] = choice
        await interaction.response.send_message("✅ Choice Saved!", ephemeral=True)

        if len(self.choices) == 2:
            c1 = self.choices[self.player1.id]
            c2 = self.choices[self.player2.id]

            if c1 == c2:
                result = t_game(interaction.user.id, "draw")
            elif (
                (c1 == "rock" and c2 == "scissors")
                or (c1 == "paper" and c2 == "rock")
                or (c1 == "scissors" and c2 == "paper")
            ):
                result = t_game(interaction.user.id, "win").format(
                    winner=self.player1.mention
                )
            else:
                result = t_game(interaction.user.id, "win").format(
                    winner=self.player2.mention
                )

            for child in self.children:
                child.disabled = True

            choices_summary = f"\n\n{self.player1.mention}: {c1}\n{self.player2.mention}: {c2}"
            await interaction.message.edit(
                content=f"{result}{choices_summary}", view=self
            )


# ==========================================
# 3. لعبة Connect Four (أربع تربح)
# ==========================================
class ConnectFourView(discord.ui.View):

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0] * 7 for _ in range(6)]  # 6 rows x 7 cols

        for col in range(7):
            self.add_item(self.ColButton(col))

    class ColButton(discord.ui.Button):

        def __init__(self, col: int):
            super().__init__(
                label=str(col + 1),
                style=discord.ButtonStyle.primary,
                row=0 if col < 4 else 1,
            )
            self.col = col

        async def callback(self, interaction: discord.Interaction):
            view: ConnectFourView = self.view

            if interaction.user not in (view.player1, view.player2):
                msg = t_game(interaction.user.id, "not_a_player")
                await interaction.response.send_message(msg, ephemeral=True)
                return

            if interaction.user != view.current_player:
                msg = t_game(interaction.user.id, "not_your_turn")
                await interaction.response.send_message(msg, ephemeral=True)
                return

            # إيجاد أول خانة فارغة في العمود من الأسفل
            row_to_place = -1
            for r in range(5, -1, -1):
                if view.board[r][self.col] == 0:
                    row_to_place = r
                    break

            if row_to_place == -1:
                msg = t_game(interaction.user.id, "c4_full")
                await interaction.response.send_message(msg, ephemeral=True)
                return

            piece = 1 if view.current_player == view.player1 else 2
            view.board[row_to_place][self.col] = piece

            if view.check_win(piece):
                for child in view.children:
                    child.disabled = True
                msg = (
                    f"{view.render_board()}\n\n"
                    + t_game(interaction.user.id, "win").format(
                        winner=view.current_player.mention
                    )
                )
                await interaction.response.edit_message(content=msg, view=view)
                view.stop()
            elif all(view.board[0][c] != 0 for c in range(7)):
                for child in view.children:
                    child.disabled = True
                msg = (
                    f"{view.render_board()}\n\n"
                    + t_game(interaction.user.id, "draw")
                )
                await interaction.response.edit_message(content=msg, view=view)
                view.stop()
            else:
                view.current_player = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                next_msg = t_game(view.current_player.id, "turn").format(
                    player=view.current_player.mention
                )
                await interaction.response.edit_message(
                    content=f"{view.render_board()}\n\n{next_msg}", view=view
                )

    def render_board(self) -> str:
        symbols = {0: "⚪", 1: "🔴", 2: "🟡"}
        res = ""
        for row in self.board:
            res += "".join(symbols[cell] for cell in row) + "\n"
        res += "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        return res

    def check_win(self, p: int) -> bool:
        # فحص أفقياً، عمودياً، وأقطار
        for r in range(6):
            for c in range(7):
                if c + 3 < 7 and all(
                    self.board[r][c + i] == p for i in range(4)
                ):
                    return True
                if r + 3 < 6 and all(
                    self.board[r + i][c] == p for i in range(4)
                ):
                    return True
                if (
                    r + 3 < 6
                    and c + 3 < 7
                    and all(self.board[r + i][c + i] == p for i in range(4))
                ):
                    return True
                if (
                    r - 3 >= 0
                    and c + 3 < 7
                    and all(self.board[r - i][c + i] == p for i in range(4))
                ):
                    return True
        return False


# ==========================================
# Cog الألعاب وتسجيل الأوامر
# ==========================================
class GamesCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- أمر XO ---
    @app_commands.command(
        name="xo", description="Start a Tic-Tac-Toe game / بدء لعبة إكس أوه"
    )
    async def xo(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        # 🟢 الشرط الأول: التجاهل التام إن لم تكن القناة هي قناة الألعاب
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Invalid opponent!", ephemeral=True
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        msg = t_game(interaction.user.id, "turn").format(
            player=interaction.user.mention
        )
        await interaction.response.send_message(msg, view=view)

    # --- أمر حجرة ورقة مقص ---
    @app_commands.command(
        name="rps",
        description="Start Rock Paper Scissors / بدء لعبة حجرة ورقة مقص",
    )
    async def rps(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        # 🟢 الشرط الأول: التجاهل التام
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Invalid opponent!", ephemeral=True
            )
            return

        view = RPSView(interaction.user, opponent)
        msg = f"🎮 **{interaction.user.mention} VS {opponent.mention}**\n{t_game(interaction.user.id, 'rps_wait')}"
        await interaction.response.send_message(msg, view=view)

    # --- أمر أربع تربح ---
    @app_commands.command(
        name="connect4",
        description="Start a Connect Four game / بدء لعبة أربع تربح",
    )
    async def connect4(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        # 🟢 الشرط الأول: التجاهل التام
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Invalid opponent!", ephemeral=True
            )
            return

        view = ConnectFourView(interaction.user, opponent)
        msg = f"{view.render_board()}\n\n" + t_game(
            interaction.user.id, "turn"
        ).format(player=interaction.user.mention)
        await interaction.response.send_message(msg, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))