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
                return data.get(str(user_id), {}).get("language", "ar")
        except Exception:
            pass
    return "ar"


# --- قاموس النصوص والكلمات المترجمة ---
TEXTS = {
    "ar": {
        "xo_title": "🎮 لعبة إكس أوه",
        "rps_title": "🎮 لعبة حجرة ورقة مقص",
        "c4_title": "🎮 لعبة أربع تربح",
        "turn": "الدور",
        "pick_move": "اختر حركتك",
        "winner": "الفائز",
        "loser": "الخاسر",
        "draw": "تعادل",
        "result": "النتيجة",
        "cant_challenge_self": "❌ لا يمكنك تحدي نفسك أو البوتات!",
        "not_your_turn": "⚠️ ليس دورك الآن!",
        "not_a_player": "⚠️ أنت لست جزءاً من هذه اللعبة!",
        "c4_full": "⚠️ هذا العمود مكتمل!",
        "win_msg": "🎉 مبروك! لقد فزت في اللعبة!",
        "lose_msg": "💔 للأسف! لقد خسرت اللعبة.",
        "draw_msg": "🤝 انتهت اللعبة بالتعادل!",
    },
    "en": {
        "xo_title": "🎮 Tic-Tac-Toe",
        "rps_title": "🎮 Rock Paper Scissors",
        "c4_title": "🎮 Connect Four",
        "turn": "Turn",
        "pick_move": "Pick your move",
        "winner": "Winner",
        "loser": "Loser",
        "draw": "Draw",
        "result": "Result",
        "cant_challenge_self": "❌ You cannot challenge yourself or a bot!",
        "not_your_turn": "⚠️ It's not your turn!",
        "not_a_player": "⚠️ You are not part of this game!",
        "c4_full": "⚠️ This column is full!",
        "win_msg": "🎉 Congratulations! You won!",
        "lose_msg": "💔 Defeat! You lost the game.",
        "draw_msg": "🤝 The game ended in a draw!",
    },
    "es": {
        "xo_title": "🎮 Tres en Raya",
        "rps_title": "🎮 Piedra Papel Tijeras",
        "c4_title": "🎮 Conecta Cuatro",
        "turn": "Turno",
        "pick_move": "Elige tu movimiento",
        "winner": "Ganador",
        "loser": "Perdedor",
        "draw": "Empate",
        "result": "Resultado",
        "cant_challenge_self": "❌ ¡No puedes desafiarte a ti mismo ni a un bot!",
        "not_your_turn": "⚠️ ¡No es tu turno!",
        "not_a_player": "⚠️ ¡No eres parte de este juego!",
        "c4_full": "⚠️ ¡Esta columna está llena!",
        "win_msg": "🎉 ¡Felicidades! ¡Ganaste!",
        "lose_msg": "💔 ¡Derrota! Perdiste el juego.",
        "draw_msg": "🤝 ¡El juego terminó en empate!",
    },
    "ja": {
        "xo_title": "🎮 ○×ゲーム",
        "rps_title": "🎮 じゃんけん",
        "c4_title": "🎮 コネクトフォー",
        "turn": "手番",
        "pick_move": "手を選んでください",
        "winner": "勝者",
        "loser": "敗者",
        "draw": "引き分け",
        "result": "結果",
        "cant_challenge_self": "❌ 自分自身やボットに挑戦することはできません！",
        "not_your_turn": "⚠️ あなたの番ではありません！",
        "not_a_player": "⚠️ あなたはこのゲームに参加していません！",
        "c4_full": "⚠️ この列はいっぱいです！",
        "win_msg": "🎉 おめでとうございます！あなたの勝ちです！",
        "lose_msg": "💔 残念！あなたの負けです。",
        "draw_msg": "🤝 引き分けで終了しました！",
    },
    "ko": {
        "xo_title": "🎮 틱택토",
        "rps_title": "🎮 가위바위보",
        "c4_title": "🎮 커넥트 포",
        "turn": "차례",
        "pick_move": "수를 선택하세요",
        "winner": "승자",
        "loser": "패자",
        "draw": "무승부",
        "result": "결과",
        "cant_challenge_self": "❌ 자신이나 봇에게 도전할 수 없습니다!",
        "not_your_turn": "⚠️ 당신의 차례가 아닙니다!",
        "not_a_player": "⚠️ 이 게임의 참가자가 아닙니다!",
        "c4_full": "⚠️ 이 열은 가득 찼습니다!",
        "win_msg": "🎉 축하합니다! 승리했습니다!",
        "lose_msg": "💔 패배했습니다!",
        "draw_msg": "🤝 무승부로 끝났습니다!",
    },
}


# --- دالة جلب النص المفصل بلغة اللاعبين الاثنين ---
def get_bi_text(p1_id: int, p2_id: int, key: str) -> str:
    lang1 = get_user_lang(p1_id)
    lang2 = get_user_lang(p2_id)

    t1 = TEXTS.get(lang1, TEXTS["ar"]).get(key, "")
    t2 = TEXTS.get(lang2, TEXTS["en"]).get(key, "")

    if lang1 == lang2 or t1 == t2:
        return t1
    return f"{t1} / {t2}"


def get_single_text(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return TEXTS.get(lang, TEXTS["ar"]).get(key, "")


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
                get_single_text(interaction.user.id, "not_a_player"),
                ephemeral=True,
            )
            return

        if interaction.user != view.current_player:
            await interaction.response.send_message(
                get_single_text(interaction.user.id, "not_your_turn"),
                ephemeral=True,
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
        title = get_bi_text(
            view.player1.id, view.player2.id, "xo_title"
        )

        if winner:
            for child in view.children:
                child.disabled = True
            loser = view.player2 if winner == view.player1 else view.player1
            w_label = get_bi_text(
                view.player1.id, view.player2.id, "winner"
            )

            content = f"{title}\n\n🏆 **{w_label}:** {winner.mention}"
            await interaction.response.edit_message(content=content, view=view)

            # إرسال إشعار فوز وخسارة مرة واحدة فقط في النهاية
            await interaction.followup.send(
                get_single_text(winner.id, "win_msg"), ephemeral=True
            )
            await interaction.followup.send(
                get_single_text(loser.id, "lose_msg"), ephemeral=True
            )
            view.stop()

        elif view.is_full():
            for child in view.children:
                child.disabled = True
            res_label = get_bi_text(
                view.player1.id, view.player2.id, "result"
            )
            draw_label = get_bi_text(
                view.player1.id, view.player2.id, "draw"
            )

            content = f"{title}\n\n🤝 **{res_label}:** {draw_label}"
            await interaction.response.edit_message(content=content, view=view)

            await interaction.followup.send(
                get_single_text(view.player1.id, "draw_msg"),
                ephemeral=True,
            )
            await interaction.followup.send(
                get_single_text(view.player2.id, "draw_msg"),
                ephemeral=True,
            )
            view.stop()

        else:
            view.current_player = next_player
            turn_label = get_bi_text(
                view.player1.id, view.player2.id, "turn"
            )

            content = f"{title}\n❌ {view.player1.mention} VS ⭕ {view.player2.mention}\n👉 **{turn_label}:** {next_player.mention}"
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
                get_single_text(interaction.user.id, "not_a_player"),
                ephemeral=True,
            )
            return

        self.choices[interaction.user.id] = choice
        # عدم إرسال إشعار خيار محفوظ لمنع الامتلاء، والاعتماد على إخفاء التفاعل
        await interaction.response.defer()

        if len(self.choices) == 2:
            c1 = self.choices[self.player1.id]
            c2 = self.choices[self.player2.id]

            emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

            for child in self.children:
                child.disabled = True

            title = get_bi_text(
                self.player1.id, self.player2.id, "rps_title"
            )
            summary = f"{title}\n{self.player1.mention} ({emoji_map[c1]}) VS {self.player2.mention} ({emoji_map[c2]})\n\n"

            if c1 == c2:
                res_label = get_bi_text(
                    self.player1.id, self.player2.id, "result"
                )
                draw_label = get_bi_text(
                    self.player1.id, self.player2.id, "draw"
                )
                summary += f"🤝 **{res_label}:** {draw_label}"
                await interaction.followup.send(
                    get_single_text(self.player1.id, "draw_msg"),
                    ephemeral=True,
                )
                await interaction.followup.send(
                    get_single_text(self.player2.id, "draw_msg"),
                    ephemeral=True,
                )
            else:
                winner = (
                    self.player1
                    if (c1 == "rock" and c2 == "scissors")
                    or (c1 == "paper" and c2 == "rock")
                    or (c1 == "scissors" and c2 == "paper")
                    else self.player2
                )
                loser = (
                    self.player2 if winner == self.player1 else self.player1
                )
                w_label = get_bi_text(
                    self.player1.id, self.player2.id, "winner"
                )

                summary += f"🏆 **{w_label}:** {winner.mention}"
                await interaction.followup.send(
                    get_single_text(winner.id, "win_msg"), ephemeral=True
                )
                await interaction.followup.send(
                    get_single_text(loser.id, "lose_msg"), ephemeral=True
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
                    get_single_text(interaction.user.id, "not_a_player"),
                    ephemeral=True,
                )
                return

            if interaction.user != view.current_player:
                await interaction.response.send_message(
                    get_single_text(interaction.user.id, "not_your_turn"),
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
                    get_single_text(interaction.user.id, "c4_full"),
                    ephemeral=True,
                )
                return

            piece = 1 if view.current_player == view.player1 else 2
            view.board[row_to_place][self.col] = piece
            title = get_bi_text(
                view.player1.id, view.player2.id, "c4_title"
            )

            if view.check_win(piece):
                for child in view.children:
                    child.disabled = True
                loser = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                w_label = get_bi_text(
                    view.player1.id, view.player2.id, "winner"
                )

                msg = f"{title}\n{view.render_board()}\n\n🏆 **{w_label}:** {view.current_player.mention}"
                await interaction.response.edit_message(content=msg, view=view)

                await interaction.followup.send(
                    get_single_text(view.current_player.id, "win_msg"),
                    ephemeral=True,
                )
                await interaction.followup.send(
                    get_single_text(loser.id, "lose_msg"), ephemeral=True
                )
                view.stop()

            elif all(view.board[0][c] != 0 for c in range(7)):
                for child in view.children:
                    child.disabled = True
                res_label = get_bi_text(
                    view.player1.id, view.player2.id, "result"
                )
                draw_label = get_bi_text(
                    view.player1.id, view.player2.id, "draw"
                )

                msg = f"{title}\n{view.render_board()}\n\n🤝 **{res_label}:** {draw_label}"
                await interaction.response.edit_message(content=msg, view=view)

                await interaction.followup.send(
                    get_single_text(view.player1.id, "draw_msg"),
                    ephemeral=True,
                )
                await interaction.followup.send(
                    get_single_text(view.player2.id, "draw_msg"),
                    ephemeral=True,
                )
                view.stop()

            else:
                view.current_player = (
                    view.player2
                    if view.current_player == view.player1
                    else view.player1
                )
                turn_label = get_bi_text(
                    view.player1.id, view.player2.id, "turn"
                )

                msg = f"{title}\n{view.render_board()}\n\n🔴 {view.player1.mention} VS 🟡 {view.player2.mention}\n👉 **{turn_label}:** {view.current_player.mention}"
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

    # --- أمر XO ---
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
                get_single_text(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        title = get_bi_text(
            interaction.user.id, opponent.id, "xo_title"
        )
        turn_label = get_bi_text(
            interaction.user.id, opponent.id, "turn"
        )

        msg = f"{title}\n❌ {interaction.user.mention} VS ⭕ {opponent.mention}\n👉 **{turn_label}:** {interaction.user.mention}"
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
                get_single_text(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = RPSView(interaction.user, opponent)
        title = get_bi_text(
            interaction.user.id, opponent.id, "rps_title"
        )
        pick_label = get_bi_text(
            interaction.user.id, opponent.id, "pick_move"
        )

        msg = f"{title}\n{interaction.user.mention} VS {opponent.mention}\n\n👇 **{pick_label}:**"
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
                get_single_text(interaction.user.id, "cant_challenge_self"),
                ephemeral=True,
            )
            return

        view = ConnectFourView(interaction.user, opponent)
        title = get_bi_text(
            interaction.user.id, opponent.id, "c4_title"
        )
        turn_label = get_bi_text(
            interaction.user.id, opponent.id, "turn"
        )

        msg = f"{title}\n{view.render_board()}\n\n🔴 {interaction.user.mention} VS 🟡 {opponent.mention}\n👉 **{turn_label}:** {interaction.user.mention}"
        await interaction.response.send_message(msg, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))