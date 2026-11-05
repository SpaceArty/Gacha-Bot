import discord
from fighting.fight_logic import Fight_Logic
from utils import guards

class FightView(guards.AuthorOnlyView):
    def __init__(self, challenger: discord.Member, opponent: discord.Member, deck1, deck2):
        super().__init__(owner=challenger, timeout=None)
        self.player1 = challenger
        self.player2 = opponent

        self.deck1 = deck1
        self.deck2 = deck2

        self.current_card1 = self.deck1[0] if self.deck1 else None
        self.current_card2 = self.deck2[0] if self.deck2 else None

        self.turn = 1
        self.current_player = self.player1
        self.current_opponent = self.player2

        self.last_action = ""

        self.skill_points1 = 3
        self.skill_points2 = 3
        self.skill_points_max = 6

        self.message = None

        self.player1_played = False
        self.player2_played = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.current_player.id:
            await interaction.response.send_message(
                "❌ Ce n'est pas ton tour !", ephemeral=True
            )
            return False
        return True

    def build_embed(self) -> discord.Embed:
        hp_emoji = "❤️"
        atk_emoji = "🗡️"
        def_emoji = "🛡️"
        filled_circle = "●"
        empty_circle = "○"

        card1_info = (
            f"**{self.current_card1.nom}** {hp_emoji}{self.current_card1.HP} "
            f"{atk_emoji}{self.current_card1.attaque} {def_emoji}{self.current_card1.defense}"
        ) if self.current_card1 else "Aucune carte"

        card2_info = (
            f"**{self.current_card2.nom}** {hp_emoji}{self.current_card2.HP} "
            f"{atk_emoji}{self.current_card2.attaque} {def_emoji}{self.current_card2.defense}"
        ) if self.current_card2 else "Aucune carte"

        sp1_display = filled_circle * self.skill_points1 + empty_circle * (self.skill_points_max - self.skill_points1)
        sp2_display = filled_circle * self.skill_points2 + empty_circle * (self.skill_points_max - self.skill_points2)

        embed = discord.Embed(
            title=f"⚔️ Tour {self.turn} - Au tour de {self.current_player.display_name}",
            description=(
                f"{self.player1.mention} : {card1_info}\n"
                f"SP : {sp1_display} ({self.skill_points1}/{self.skill_points_max})\n"
                f"{self.player2.mention} : {card2_info}\n"
                f"SP : {sp2_display} ({self.skill_points2}/{self.skill_points_max})\n\n"
                f"**Dernière action :** {self.last_action if self.last_action else '...'}"
            ),
            color=discord.Color.orange()
        )
        return embed

    def next_turn(self):
        # Si player1 vient de jouer
        if not self.player1_played:
            self.player1_played = True
            self.current_player = self.player2
            self.current_opponent = self.player1
        # Si player1 a déjà joué, c'est que player2 vient de finir son tour
        else:
            self.player2_played = True
            self.current_player = self.player1
            self.current_opponent = self.player2
            # Les deux ont joué -> nouveau tour
            self.turn += 1
            self.player1_played = False
            self.player2_played = False

    # ----- Bouton attaque -----
    @discord.ui.button(label="🗡️ Attaquer", style=discord.ButtonStyle.danger)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérifier que c'est bien le joueur actuel qui clique
        if interaction.user.id != self.current_player.id:
            await interaction.response.send_message("Ce n'est pas votre tour !", ephemeral=True)
            return
        
        logic = Fight_Logic()

        if self.current_player == self.player1:
            self.current_card1, self.current_card2 = logic.attack(self.current_card1, self.current_card2)
            attacker_card = self.current_card1
            defender_card = self.current_card2
        else:
            self.current_card2, self.current_card1 = logic.attack(self.current_card2, self.current_card1)
            attacker_card = self.current_card2
            defender_card = self.current_card1

        self.last_action = f"🗡️ {self.current_player.display_name} attaque {self.current_opponent.display_name} avec **{attacker_card.nom}**, PV restants : {defender_card.HP}"

        self.next_turn()
        # On répond à l'interaction pour éviter "échec de l'interaction"
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ----- Bouton capacité -----
    @discord.ui.button(label="✨ Capacité", style=discord.ButtonStyle.primary)
    async def ability_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_player == self.player1:
            if self.skill_points1 > 0:
                self.skill_points1 -= 1
        else:
            if self.skill_points2 > 0:
                self.skill_points2 -= 1

        self.last_action = f"✨ {interaction.user.display_name} utilise sa capacité !"

        self.next_turn()

        await interaction.response.edit_message(embed=self.build_embed(), view=self)