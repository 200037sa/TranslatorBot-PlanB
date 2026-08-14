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
                return data.get(str(user_id), {}).get("language", "en")
        except Exception:
            pass
    return "en"


# --- نصوص الألعاب بجميع اللغات المدعومة (تظهر خاصة بكل لاعب Ephemeral) ---
GAME_TRANSLATIONS = {
    "ar": {
        "cant_challenge_self": "❌ لا يمكنك تحدي نفسك أو البوتات!",
        "not_your_turn": "⚠️ ليس دورك الآن! انتظر خصمك.",
        "not_a_player": "⚠️ أنت لست جزءاً من هذه اللعبة!",
        "win": "🎉 مبروك! لقد فزت في اللعبة!",
        "lose": "💔 للأسف! لقد خسرت اللعبة.",
        "draw": "🤝 انتهت اللعبة بالتعادل!",
        "your_turn_prompt": "🎮 دورك الآن! اختر حركتك.",
        "choice_saved": "✅ تم تسجيل اختيارك بنجاح!",
        "c4_full": "⚠️ هذا العمود مكتمل، اختر عموداً آخر!",
        "game_started": "🎮 بدأت اللعبة بين {p1} و {p2}!",
    },
    "en": {
        "cant_challenge_self": "❌ You cannot challenge yourself or a bot!",
        "not_your_turn": "⚠️ It's not your turn! Wait for your opponent.",
        "not_a_player": "⚠️ You are not part of this game!",
        "win": "🎉 Congratulations! You won the game!",
        "lose": "💔 Defeat! You lost the game.",
        "draw": "🤝 The game ended in a draw!",
        "your_turn_prompt": "🎮 It's your turn! Make a move.",
        "choice_saved": "✅ Your choice has been saved!",
        "c4_full": "⚠️ This column is full, pick another one!",
        "game_started": "🎮 Game started between {p1} and {p2}!",
    },
    "es": {
        "cant_challenge_self": "❌ ¡No puedes desafiarte a ti mismo ni a un bot!",
        "not_your_turn": "⚠️ ¡No es tu turno! Espera a tu oponente.",
        "not_a_player": "⚠️ ¡No eres parte de este juego!",
        "win": "🎉 ¡Felicidades! ¡Ganaste el juego!",
        "lose": "💔 ¡Derrota! Perdiste el juego.",
        "draw": "🤝 ¡El juego terminó en empate!",
        "your_turn_prompt": "🎮 ¡Es tu turno! Haz tu movimiento.",
        "choice_saved": "✅ ¡Tu elección ha sido guardada!",
        "c4_full": "⚠️ ¡Esta columna está llena, elige otra!",
        "game_started": "🎮 ¡Juego iniciado entre {p1} y {p2}!",
    },
    "ja": {
        "cant_challenge_self": "❌ 自分自身やボットに挑戦することはできません！",
        "not_your_turn": "⚠️ あなたの番ではありません！相手を待ってください。",
        "not_a_player": "⚠️ あなたはこのゲームに参加していません！",
        "win": "🎉 おめでとうございます！あなたの勝ちです！",
        "lose": "💔 残念！あなたの負けです。",
        "draw": "🤝 引き分けでゲームが終了しました！",
        "your_turn_prompt": "🎮 あなたの番です！手を選んでください。",
        "choice_saved": "✅ 選択が保存されました！",
        "c4_full": "⚠️ この列はいっぱいです。別の列を選んでください！",
        "game_started": "🎮 {p1} と {p2} のゲームが始まりました！",
    },
    "ko": {
        "cant_challenge_self": "❌ 자신이나 봇에게 도전할 수 없습니다!",
        "not_your_turn": "⚠️ 당신의 차례가 아닙니다! 상대방을 기다리세요.",
        "not_a_player": "⚠️ 이 게임의 참가자가 아닙니다!",
        "win": "🎉 축하합니다! 게임에서 승리했습니다!",
        "lose": "💔 패배했습니다! 게임에서 졌습니다.",
        "draw": "🤝 게임이 비겼습니다!",
        "your_turn_prompt": "🎮 당신의 차례입니다! 수를 두세요.",
        "choice_saved": "✅ 선택이 저장되었습니다!",
        "c4_full": "⚠️ 이 열은 가득 찼습니다. 다른 열을 선택하세요!",
        "game_started": "🎮 {p1} 님과 {p2} 님의 게임이 시작되었습니다!",
    },
}


def t_game(user_id: int, key: str, **kwargs) -> str:
    lang = get_user_lang(user_id)
    text = GAME_TRANSLATIONS.get(lang, GAME_TRANSLATIONS["en"]).get(key, "")
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

        # تحقق مما إذا كان الضاغط لاعب أساسي
        if interaction.user not in (view.player1, view.player2):
            await interaction.response.send_message(
                t_game(interaction.user.id, "not_a_player"), ephemeral=True
            )
            return

        # تحقق من الدور
        if interaction.user != view.current_player:
            await interaction.response.send_message(
                t_game(interaction.user.id, "not_your_turn"), ephemeral=True
            )
            return

        if view.board[self.y][self.x] != 0:
            return

        # وضع الرمز
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

            loser = view.player2 if winner == view.player1 else view.player1

            # إرسال رسالة عامة بسيطة بأسماء اللاعبين والنتيجة
            content = f"🎮 **Tic-Tac-Toe**\n🏆 **Winner:** {winner.mention}\n💀 **Loser:** {loser.mention}"
            await interaction.response.edit_message(content=content, view=view)

            # إرسال تنبيه خاص ومترجم بالفوز/الخسارة لكل لاعب
            await interaction.followup.send(
                t_game(winner.id, "win"), ephemeral=True
            )
            await interaction.followup.send(
                t_game(loser.id, "lose"), ephemeral=True
            )
            view.stop()

        elif view.is_full():
            for child in view.children:
                child.disabled = True
            content = f"🎮 **Tic-Tac-Toe**\n🤝 **Result:** Draw / تعادل"
            await interaction.response.edit_message(content=content, view=view)
            view.stop()

        else:
            view.current_player = next_player
            # رسالة الواجهة العامة تعتمد على المنشن والإيموجي فقط تجنباً للخبطة اللغات
            content = f"🎮 **Tic-Tac-Toe**\n❌ {view.player1.mention} VS ⭕ {view.player2.mention}\n👉 **Turn:** {next_player.mention}"
            await interaction.response.edit_message(content=content, view=view)

            # تنبيه خاص للاعب صاحب الدور بلغته هو فقط
            await interaction.followup.send(
                t_game(next_player.id, "your_turn_prompt"), ephemeral=True
            )


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
                t_game(interaction.user.id, "not_a_player"), ephemeral=True
            )
            return

        self.choices[interaction.user.id] = choice
        # تأكيد خاص ومترجم بلغته هو
        await interaction.response.send_message(
            t_game(interaction.user.id, "choice_saved"), ephemeral=True
        )

        if len(self.choices) == 2:
            c1 = self.choices[self.player1.id]
            c2 = self.choices[self.player2.id]

            emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

            for child in self.children:
                child.disabled = True

            summary = f"🎮 **Rock Paper Scissors**\n{self.player1.mention} ({emoji_map[c1]}) VS {self.player2.mention} ({emoji_map[c2]})\n\n"

            if c1 == c2:
                summary += "🤝 **Result:** Draw / تعادل"
            elif (
                (c1 == "rock" and c2 == "scissors")
                or (c1 == "paper" and c2 == "rock")
                or (c1 == "scissors" and c2 == "paper")
            ):
                summary += f"🏆 **Winner:** {self.player1.mention}"
                await interaction.followup.send(
                    t_game(self.player1.id, "win"), ephemeral=True
                )
                await interaction.followup.send(
                    t_game(self.player2.id, "lose"), ephemeral=True
                )
            else:
                summary += f"🏆 **Winner:** {self.player2.mention}"
                await interaction.followup.send(
                    t_game(self.player2.id, "win"), ephemeral=True
                )
                await interaction.followup.send(
                    t_game(self.player1.id, "lose"), ephemeral=True
                )

            await interaction.message.edit(content=summary, view=self)


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
                    t_game(interaction.user.id, "not_a_player"),
                    ephemeral=True,
                )
                return

            if interaction.user != view.current_player:
                await interaction.response.send_message(
                    t_game(interaction.user.id, "not_your_turn"),
                    ephemeral=True,
                )
                return

            row_to_place = -1
            for r in range(5, -1, -1):
                if view.board[r][self.col] == 0:
                    row_to_place = r
                    break

            if row_to_place == -1:
                await interaction.response.send_message(
                    t_game(interaction.user.id, "c4_full"), ephemeral=True
                )
                return

            piece = 1 if view.current_player == view.player1 else 2
            view.board[row_to_place][self.col] = piece

            if view.check_win(piece):
                for child in view.children:
                    child.disabled = True
                loser = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                msg = f"{view.render_board()}\n\n🏆 **Winner:** {view.current_player.mention}"
                await interaction.response.edit_message(content=msg, view=view)

                await interaction.followup.send(
                    t_game(view.current_player.id, "win"), ephemeral=True
                )
                await interaction.followup.send(
                    t_game(loser.id, "lose"), ephemeral=True
                )
                view.stop()

            elif all(view.board[0][c] != 0 for c in range(7)):
                for child in view.children:
                    child.disabled = True
                msg = f"{view.render_board()}\n\n🤝 **Result:** Draw / تعادل"
                await interaction.response.edit_message(content=msg, view=view)
                view.stop()

            else:
                view.current_player = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                msg = f"{view.render_board()}\n\n🔴 {view.player1.mention} VS 🟡 {view.player2.mention}\n👉 **Turn:** {view.current_player.mention}"
                await interaction.response.edit_message(content=msg, view=view)

                await interaction.followup.send(
                    t_game(view.current_player.id, "your_turn_prompt"),
                    ephemeral=True,
                )

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

    # --- أمر XO ---
    @app_commands.command(
        name="xo", description="Start a Tic-Tac-Toe game / بدء لعبة إكس أوه"
    )
    async def xo(
        self, interaction: discord.Interaction, opponent: discord.User
    ):
        if interaction.channel_id != GAMES_CHANNEL_ID:
            return

        # منع تحدي النفس أو البوتات فوراً وبشكل خاص
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                t_game(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        msg = f"🎮 **Tic-Tac-Toe**\n❌ {interaction.user.mention} VS ⭕ {opponent.mention}\n👉 **Turn:** {interaction.user.mention}"
        await interaction.response.send_message(msg, view=view)

    # --- أمر حجرة ورقة مقص ---
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
                t_game(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = RPSView(interaction.user, opponent)
        msg = f"🎮 **Rock Paper Scissors**\n{interaction.user.mention} VS {opponent.mention}\n\n👇 Pick your move below / اختر حركتك بالأسفل:"
        await interaction.response.send_message(msg, view=view)

    # --- أمر أربع تربح ---
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
                t_game(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = ConnectFourView(interaction.user, opponent)
        msg = f"{view.render_board()}\n\n🔴 {interaction.user.mention} VS 🟡 {opponent.mention}\n👉 **Turn:** {interaction.user.mention}"
        await interaction.response.send_message(msg, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))