import json
import os
import discord
from discord import app_commands
from discord.ext import commands

# ⚠️ ضع هنا آيدي قناة الألعاب الخاصة بالسيرفر
GAMES_CHANNEL_ID = 1537829034065403925  # استبدل هذا الرقم بـ ID قناة الألعاب لديك

DATA_FILE = "user_profiles.json"


def get_user_lang(interaction: discord.Interaction) -> str:
    """جلب اللغة إما من ملف البيانات الخاص بالبوات أو من لغة تطبيق ديسكورد للمستخدم مباشرة"""
    user_id = str(interaction.user.id)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if user_id in data and "language" in data[user_id]:
                    return data[user_id]["language"]
        except Exception:
            pass

    # إذا لم توجد في الملف، نأخذ لغة تطبيق ديسكورد الخاص به
    locale = str(interaction.locale).split("-")[0]
    return locale if locale in GAME_TRANSLATIONS else "ar"


GAME_TRANSLATIONS = {
    "ar": {
        "cant_challenge_self": "❌ لا يمكنك تحدي نفسك أو البوتات!",
        "not_your_turn": "⚠️ ليس دورك الآن! انتظر خصمك.",
        "not_a_player": "⚠️ أنت لست جزءاً من هذه اللعبة!",
        "win": "🎉 فاز {winner}!",
        "draw": "🤝 تعادل!",
        "c4_full": "⚠️ هذا العمود مكتمل، اختر عموداً آخر!",
    },
    "en": {
        "cant_challenge_self": "❌ You cannot challenge yourself or a bot!",
        "not_your_turn": "⚠️ It's not your turn! Wait for your opponent.",
        "not_a_player": "⚠️ You are not part of this game!",
        "win": "🎉 {winner} won!",
        "draw": "🤝 It's a draw!",
        "c4_full": "⚠️ This column is full, pick another one!",
    },
    "es": {
        "cant_challenge_self": "❌ ¡No puedes desafiarte a ti mismo ni a un bot!",
        "not_your_turn": "⚠️ ¡No es tu turno! Espera a tu oponente.",
        "not_a_player": "⚠️ ¡No eres parte de este juego!",
        "win": "🎉 ¡{winner} ha ganado!",
        "draw": "🤝 ¡Empate!",
        "c4_full": "⚠️ ¡Esta columna está llena, elige otra!",
    },
    "ja": {
        "cant_challenge_self": "❌ 自分自身やボットに挑戦することはできません！",
        "not_your_turn": "⚠️ あなたの番ではありません！相手を待ってください。",
        "not_a_player": "⚠️ あなたはこのゲームに参加していません！",
        "win": "🎉 {winner} の勝利！",
        "draw": "🤝 引き分け！",
        "c4_full": "⚠️ この列はいっぱいです。別の列を選んでください！",
    },
    "ko": {
        "cant_challenge_self": "❌ 자신이나 봇에게 도전할 수 없습니다!",
        "not_your_turn": "⚠️ 당신의 차례가 아닙니다! 상대방을 기다리세요.",
        "not_a_player": "⚠️ 이 게임의 참가자가 아닙니다!",
        "win": "🎉 {winner} 님의 승리!",
        "draw": "🤝 비겼습니다!",
        "c4_full": "⚠️ 이 열은 가득 찼습니다. 다른 열을 선택하세요!",
    },
}


def t_game(interaction: discord.Interaction, key: str, **kwargs) -> str:
    lang = get_user_lang(interaction)
    text = GAME_TRANSLATIONS.get(lang, GAME_TRANSLATIONS["ar"]).get(key, "")
    return text.format(**kwargs) if kwargs else text


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
            await interaction.response.send_message(
                t_game(interaction, "not_a_player"), ephemeral=True
            )
            return

        if interaction.user != view.current_player:
            await interaction.response.send_message(
                t_game(interaction, "not_your_turn"), ephemeral=True
            )
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
            content = f"🎮 **Tic-Tac-Toe**\n🏆 {t_game(interaction, 'win', winner=winner.mention)}"
            await interaction.response.edit_message(content=content, view=view)
            view.stop()

        elif view.is_full():
            for child in view.children:
                child.disabled = True
            content = f"🎮 **Tic-Tac-Toe**\n🤝 {t_game(interaction, 'draw')}"
            await interaction.response.edit_message(content=content, view=view)
            view.stop()

        else:
            view.current_player = next_player
            content = f"🎮 **Tic-Tac-Toe**\n❌ {view.player1.mention} VS ⭕ {view.player2.mention}\n👉 **Turn / الدور:** {next_player.mention}"
            await interaction.response.edit_message(content=content, view=view)


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

    @discord.ui.button(label="🪨", style=discord.ButtonStyle.primary)
    async def rock(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "rock")

    @discord.ui.button(label="📄", style=discord.ButtonStyle.primary)
    async def paper(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "paper")

    @discord.ui.button(label="✂️", style=discord.ButtonStyle.primary)
    async def scissors(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.make_choice(interaction, "scissors")

    async def make_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user not in (self.player1, self.player2):
            await interaction.response.send_message(
                t_game(interaction, "not_a_player"), ephemeral=True
            )
            return

        self.choices[interaction.user.id] = choice

        if len(self.choices) == 1:
            # تحديث الرسالة الأصلية نفسها بدلاً من إضافة إشعار جديد
            waiting_user = (
                self.player2
                if interaction.user == self.player1
                else self.player1
            )
            await interaction.response.edit_message(
                content=f"🎮 **Rock Paper Scissors**\n{self.player1.mention} VS {self.player2.mention}\n\n⏳ **Waiting for / في انتظار:** {waiting_user.mention}",
                view=self,
            )

        elif len(self.choices) == 2:
            c1 = self.choices[self.player1.id]
            c2 = self.choices[self.player2.id]
            emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

            for child in self.children:
                child.disabled = True

            summary = f"🎮 **Rock Paper Scissors**\n{self.player1.mention} ({emoji_map[c1]}) VS {self.player2.mention} ({emoji_map[c2]})\n\n"

            if c1 == c2:
                summary += f"🤝 {t_game(interaction, 'draw')}"
            elif (
                (c1 == "rock" and c2 == "scissors")
                or (c1 == "paper" and c2 == "rock")
                or (c1 == "scissors" and c2 == "paper")
            ):
                summary += f"🏆 {t_game(interaction, 'win', winner=self.player1.mention)}"
            else:
                summary += f"🏆 {t_game(interaction, 'win', winner=self.player2.mention)}"

            await interaction.response.edit_message(content=summary, view=self)


# ==========================================
# 3. لعبة Connect Four (أربع تربح)
# ==========================================
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
                row=0 if col < 4 else 1,
            )
            self.col = col

        async def callback(self, interaction: discord.Interaction):
            view: ConnectFourView = self.view

            if interaction.user not in (view.player1, view.player2):
                await interaction.response.send_message(
                    t_game(interaction, "not_a_player"), ephemeral=True
                )
                return

            if interaction.user != view.current_player:
                await interaction.response.send_message(
                    t_game(interaction, "not_your_turn"), ephemeral=True
                )
                return

            row_to_place = -1
            for r in range(5, -1, -1):
                if view.board[r][self.col] == 0:
                    row_to_place = r
                    break

            if row_to_place == -1:
                await interaction.response.send_message(
                    t_game(interaction, "c4_full"), ephemeral=True
                )
                return

            piece = 1 if view.current_player == view.player1 else 2
            view.board[row_to_place][self.col] = piece

            if view.check_win(piece):
                for child in view.children:
                    child.disabled = True
                msg = f"{view.render_board()}\n\n🏆 {t_game(interaction, 'win', winner=view.current_player.mention)}"
                await interaction.response.edit_message(content=msg, view=view)
                view.stop()

            elif all(view.board[0][c] != 0 for c in range(7)):
                for child in view.children:
                    child.disabled = True
                msg = (
                    f"{view.render_board()}\n\n🤝 {t_game(interaction, 'draw')}"
                )
                await interaction.response.edit_message(content=msg, view=view)
                view.stop()

            else:
                view.current_player = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                msg = f"{view.render_board()}\n\n🔴 {view.player1.mention} VS 🟡 {view.player2.mention}\n👉 **Turn / الدور:** {view.current_player.mention}"
                await interaction.response.edit_message(content=msg, view=view)

    def render_board(self) -> str:
        symbols = {0: "⚪", 1: "🔴", 2: "🟡"}
        res = ""
        for row in self.board:
            res += "".join(symbols[cell] for cell in row) + "\n"
        res += "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        return res

    def check_win(self, p: int) -> bool:
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

    @app_commands.command(
        name="xo", description="Start a Tic-Tac-Toe game / بدء لعبة إكس أوه"
    )
    async def xo(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                t_game(interaction, "cant_challenge_self"), ephemeral=True
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        msg = f"🎮 **Tic-Tac-Toe**\n❌ {interaction.user.mention} VS ⭕ {opponent.mention}\n👉 **Turn / الدور:** {interaction.user.mention}"
        await interaction.response.send_message(msg, view=view)

    @app_commands.command(
        name="rps",
        description="Start Rock Paper Scissors / بدء لعبة حجرة ورقة مقص",
    )
    async def rps(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                t_game(interaction, "cant_challenge_self"), ephemeral=True
            )
            return

        view = RPSView(interaction.user, opponent)
        msg = f"🎮 **Rock Paper Scissors**\n{interaction.user.mention} VS {opponent.mention}\n\n👇 Pick your move / اختر حركتك:"
        await interaction.response.send_message(msg, view=view)

    @app_commands.command(
        name="connect4",
        description="Start a Connect Four game / بدء لعبة أربع تربح",
    )
    async def connect4(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                t_game(interaction, "cant_challenge_self"), ephemeral=True
            )
            return

        view = ConnectFourView(interaction.user, opponent)
        msg = f"{view.render_board()}\n\n🔴 {interaction.user.mention} VS 🟡 {opponent.mention}\n👉 **Turn / الدور:** {interaction.user.mention}"
        await interaction.response.send_message(msg, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))