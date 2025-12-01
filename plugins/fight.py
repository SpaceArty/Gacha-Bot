import discord; import random
from discord.ui import View, Button
from discord.ext import commands
from fighting import fighting
from utils import load, guards, config

class FightRequestView(guards.AuthorOnlyView):
    def __init__(self, challenger: discord.Member, opponent: discord.Member):
        super().__init__(owner=challenger, timeout=None)
        self.challenger = challenger
        self.opponent = opponent
        self.challenger_deck = None
        self.opponent_deck = None
        self.current_selector = None  # Sera défini après acceptation

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Si on est en phase de sélection de deck, vérifier que c'est le bon joueur
        if self.current_selector and interaction.user.id != self.current_selector.id:
            await interaction.response.send_message( "❌ Ce n'est pas ton tour pour choisir le deck !", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Si c'est un combat contre soi-même, montrer les decks directement deux fois
        if self.challenger.id == self.opponent.id:
            self.current_selector = self.challenger
            await self.show_decks_self_duel(interaction, first_selection=True)
        else:
            self.current_selector = self.challenger
            await self.show_decks(interaction, player=self.challenger)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.mention} a refusé le duel contre {self.challenger.mention}.",
            view=None
        )

    async def show_decks(self, interaction: discord.Interaction, player: discord.Member, already_responded: bool = False):
        decks = load.player_decks.get(str(player.id), {})
        legal_decks = [
            (deck_key, deck_data.get("name", deck_key))
            for deck_key, deck_data in decks.items()
            if await guards.checkDeckLegal(interaction, deck_data["cards"])
        ]

        #Créer une nouvelle View avec boutons des decks
        deck_view = discord.ui.View(timeout=None)
        for deck_key, deck_label in legal_decks:
            button = discord.ui.Button(label=deck_label, style=discord.ButtonStyle.primary)
            button.callback = self.make_deck_callback(player, deck_key, deck_label)
            deck_view.add_item(button)

        # Déterminer la couleur de l'embed selon le joueur
        embed_color = discord.Color.green() if player.id == self.challenger.id else discord.Color.red()
        
        embed = discord.Embed(
            description=f"⚔️ {player.mention}, choisis ton deck :",
            color=embed_color
        )

        # Éditer le message original pour afficher les decks
        if already_responded:
            await interaction.edit_original_response(content=None, embed=embed, view=deck_view)
        else:
            await interaction.response.edit_message(content=None, embed=embed, view=deck_view)

    async def show_decks_self_duel(self, interaction: discord.Interaction, first_selection: bool = True, already_responded: bool = False):
        decks = load.player_decks.get(str(self.challenger.id), {})
        legal_decks = [
            (deck_key, deck_data.get("name", deck_key))
            for deck_key, deck_data in decks.items()
            if await guards.checkDeckLegal(interaction, deck_data["cards"])
        ]

        # Créer une nouvelle View avec boutons des decks
        deck_view = discord.ui.View(timeout=None)
        for deck_key, deck_label in legal_decks:
            button = discord.ui.Button(label=deck_label, style=discord.ButtonStyle.primary)
            button.callback = self.make_self_duel_callback(deck_key, deck_label, first_selection)
            deck_view.add_item(button)

        # Couleur et message différents selon la sélection
        if first_selection:
            embed_color = discord.Color.green()
            description = f"⚔️ {self.challenger.mention}, choisis ton premier deck :"
        else:
            embed_color = discord.Color.red()
            description = f"⚔️ {self.challenger.mention}, choisis ton second deck :"

        embed = discord.Embed(
            description=description,
            color=embed_color
        )

        # Éditer le message original pour afficher les decks
        if already_responded:
            await interaction.edit_original_response(content=None, embed=embed, view=deck_view)
        else:
            await interaction.response.edit_message(content=None, embed=embed, view=deck_view)

    def make_self_duel_callback(self, deck_key: str, deck_label: str, is_first_selection: bool):
        async def callback(interaction: discord.Interaction):
            if is_first_selection:
                self.challenger_deck = deck_key
                await self.show_decks_self_duel(interaction, first_selection=False, already_responded=False)
            else:
                self.opponent_deck = deck_key

                # Créer une nouvelle view pour annoncer le combat
                duel_view = discord.ui.View(timeout=None)

                embed = discord.Embed(
                    description="⚔️ Les decks sont choisis ! Le combat va commencer !",
                    color=discord.Color.blurple()
                )

                await interaction.response.edit_message(embed=embed, view=duel_view)
                # Appel de ta fonction de combat ici
                fighting.start_fight(self, self.challenger, self.opponent, self.challenger_deck, self.opponent_deck)
        return callback

    def make_deck_callback(self, player: discord.Member, deck_key: str, deck_label: str):
        async def callback(interaction: discord.Interaction):
            if player.id == self.challenger.id:
                self.challenger_deck = deck_key
            else:
                self.opponent_deck = deck_key

            # Passer au joueur suivant ou lancer le duel si les deux ont choisi
            if player.id == self.challenger.id:
                self.current_selector = self.opponent
                await self.show_decks(interaction, player=self.opponent, already_responded=False)
            else:
                # Créer une nouvelle view pour annoncer le combat
                duel_view = discord.ui.View(timeout=None)

                embed = discord.Embed(
                    description="⚔️ Les decks sont choisis ! Le combat va commencer !",
                    color=discord.Color.blurple()
                )

                await interaction.response.edit_message(embed=embed, view=duel_view)
                # Appel de ta fonction de combat ici
                fighting.start_fight(self, self.challenger, self.opponent, self.challenger_deck, self.opponent_deck)
        return callback

class Fight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["f"]) # <----------------------------------------------------------- COMMANDE FIGHT
    async def fight(self, ctx, opponent: discord.Member = None):
        author = ctx.author
        opponent = opponent or author  # duel contre soi-même autorisé

        player_decks = load.player_decks

        # Vérification de l'existence des decks
        author_id = str(author.id)
        opponent_id = str(opponent.id)

        player_decks = await guards.checkDecks(author_id, player_decks) # Vérifie les deck de l'author
        player_decks = await guards.checkDecks(opponent_id, player_decks) # Vérifie les deck de l'opponent

        author_decks = player_decks[author_id]
        opponent_decks = player_decks[opponent_id]

        # Vérifier que l'author possède au moins 1 deck légal
        author_has_legal = False
        for deck in author_decks.values():
            if await guards.checkDeckLegal(ctx, deck["cards"]):
                author_has_legal = True
                break
        if not author_has_legal:
            await ctx.send(f"❌ {author.mention}, tu n'as **aucun deck légal** (6 cartes).", ephemeral=True)
            return

        # Vérifier que l'adversaire possède au moins 1 deck légal
        opponent_has_legal = False
        for deck in opponent_decks.values():
            if await guards.checkDeckLegal(ctx, deck["cards"]):
                opponent_has_legal = True
                break
        if not opponent_has_legal:
            await ctx.send(f"❌ {opponent.mention} n'a **aucun deck légal** (6 cartes).", ephemeral=True)
            return

        if opponent == author: # Embed d'annonce
            description = f"⚔️ {author.mention} veut s'entraîner seul !"
        else:
            description = f"⚔️ {author.mention} défie {opponent.mention} en duel !"

        embed = discord.Embed(
            title="Défi de duel",
            description=description,
            color=discord.Color.orange()
        )

        # Duel avec quelqu’un → envoyer la view d’acceptation
        view = FightRequestView(challenger=author, opponent=opponent)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Fight(bot)) # Ajoute le cog Fight au bot