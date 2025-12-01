import discord; from discord.ext import commands
from discord.ui import View, Button
from utils import load, guards, config

class AddCardModal(discord.ui.Modal, title="➕ Ajouter une carte"):
    def __init__(self, view, deck_key, cards):
        super().__init__()
        self.view = view 
        self.deck_key = deck_key
        self.cards = cards

        # Champs du modal
        self.card_name = discord.ui.TextInput(
            label="Nom de la carte",
            placeholder="Ex: Cricri, Dejan, Nathan, etc...",
            required=True,
            max_length=50
        )

        self.card_position = discord.ui.TextInput(
            label="Position dans le deck",
            placeholder="Entrez un numero entre 1-6",
            required=True,
            max_length=1
        )

        self.add_item(self.card_name)
        self.add_item(self.card_position)

    async def on_submit(self, interaction: discord.Interaction):
        ctx = self.view.ctx
        user_id = str(ctx.author.id)
        decks = self.view.decks
        deck_data = decks[self.view.current_deck]
        deck_cards = deck_data["cards"]

        # −−− Vérification de la position −−−
        try:
            pos = int(self.card_position.value)
            if pos <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ La position doit être entre **1 et 6**.", ephemeral=True)
            return

        # −−− Vérification de la carte via checkCard −−−
        cards_dict = self.cards
        if callable(cards_dict):
            cards_dict = cards_dict()

        card_info = await guards.checkCard(ctx, self.card_name.value, cards_dict)
        if not card_info:
            await interaction.response.send_message("❌ La carte n'existe pas.", ephemeral=True)
            return
        real_name, rarity, image_url, color = card_info

        # −−− Vérification que l'utilisateur possède la carte dans son inventaire −−−
        player_inventory = load.player_inventory
        player_inventory = await guards.checkInventory(user_id, player_inventory)
        inventory = player_inventory[user_id]

        card_entry = inventory.get(real_name)
        if not card_entry or card_entry.get("count", 0) <= 0:
            await interaction.response.send_message(f"❌ Tu ne possèdes pas la carte **{real_name}** dans ton inventaire.", ephemeral=True)
            return

        # −−− Vérification que la carte n'est pas déjà dans le deck −−−
        if any(c['name'] == real_name for c in deck_cards.values()):
            await interaction.response.send_message(f"❌ La carte **{real_name}** est déjà présente dans ce deck.", ephemeral=True)
            return


        # −−− Ajout simplifié : nom + emoji −−−
        emoji = config.RARITY_EMOJIS.get(rarity, "")
        deck_cards[str(pos)] = {
            "name": real_name,
            "emoji": emoji
        }
        load.save_decks()

        # Mise à jour de l'affichage deck
        if deck_cards:
            description_lines = [
                f"{p} → {c['emoji']} {c['name']}"
                for p, c in sorted(deck_cards.items(), key=lambda x: int(x[0]))
            ]
            description = "\n".join(description_lines)
        else:
            description = "❌ Ce deck est vide."


        embed = discord.Embed(
            title=f"📦 Deck mis à jour : {deck_data['name']}",  # <-- affiche le nom custom
            description=description,
            color=discord.Color.blurple()
        )

        self.view.show_deck_controls()
        await interaction.response.edit_message(embed=embed, view=self.view)

class RemoveCardModal(discord.ui.Modal, title="❌ Retirer une carte du deck"):
    def __init__(self, view, deck_key):
        super().__init__()
        self.view = view
        self.deck_key = deck_key

        # Champ pour la position
        self.card_position = discord.ui.TextInput(
            label="Position de la carte à retirer",
            placeholder="Entrez le numéro de la carte",
            required=True,
            max_length=4
        )
        self.add_item(self.card_position)

    async def on_submit(self, interaction: discord.Interaction):
        deck = self.view.decks[self.deck_key]

        # Vérification de la position
        try:
            pos = int(self.card_position.value)
            if pos <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ La position doit être entre **1 et 6**.", ephemeral=True)
            return

        # Supprime la carte si elle existe
        if str(pos) in deck:
            removed_card = deck.pop(str(pos))
            load.save_decks()
        else:
            removed_card = None

        # Mise à jour de l'affichage
        if deck:
            description_lines = [
                f"{p} → {c['emoji']} {c['name']}"
                for p, c in sorted(deck.items(), key=lambda x: int(x[0]))
            ]
            description = "\n".join(description_lines)
        else:
            description = "❌ Ce deck est vide."

        embed = discord.Embed(
            title=f"📦 Deck mis à jour : {self.deck_key}",
            description=description,
            color=discord.Color.blurple()
        )

        self.view.show_deck_controls()
        await interaction.response.edit_message(embed=embed, view=self.view)

class RenameDeckModal(discord.ui.Modal, title="✏️ Renommer le deck"):
    def __init__(self, view, deck_key):
        super().__init__()
        self.view = view
        self.deck_key = deck_key

        self.new_name_input = discord.ui.TextInput(
            label="Nouveau nom du deck",
            placeholder="Entrez le nouveau nom",
            required=True,
            max_length=50
        )
        self.add_item(self.new_name_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.new_name_input.value.strip()
        if not new_name:
            await interaction.response.send_message("❌ Le nom ne peut pas être vide.", ephemeral=True)
            return

        # Récupère le deck actuel
        deck_data = self.view.decks[self.deck_key]  # deck_key = 'deck1', 'deck2', etc.
        
        # Change uniquement le nom custom
        deck_data["name"] = new_name
        load.save_decks()

        # Prépare l'affichage des cartes
        deck_cards = deck_data["cards"]
        if deck_cards:
            description_lines = [
                f"{pos} → {c['emoji']} {c['name']}"
                for pos, c in sorted(deck_cards.items(), key=lambda x: int(x[0]))
            ]
            description = "\n".join(description_lines)
        else:
            description = "❌ Ce deck est vide."

        embed = discord.Embed(
            title=f"📦 Deck : {new_name}",
            description=description,
            color=discord.Color.blurple()
        )

        # Met à jour la vue
        self.view.show_deck_controls()
        self.view.current_deck = self.deck_key  # on garde la référence à la clé
        await interaction.response.edit_message(embed=embed, view=self.view)

class DeckView(guards.AuthorOnlyView):
    def __init__(self, ctx, decks, can_edit: bool):
        super().__init__(owner=ctx.author)
        self.ctx = ctx
        self.decks = decks  # Tous les decks du joueur
        self.current_deck = None  # Aucun deck sélectionné au début
        self.can_edit = can_edit
        self.show_deck_list()

    def show_deck_list(self):
        self.clear_items()  # Enlève tous les boutons actuels
        self.current_deck = None

        for i in range(1, 7):
            deck_key = f"deck{i}"
            deck_data = self.decks.get(deck_key, {"name": f"Deck {i}"})
            deck_name = deck_data.get("name", f"Deck {i}")  # nom custom ou fallback

            button = Button(
                label=deck_name,
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_deck_callback(i)
            self.add_item(button)

    def make_deck_callback(self, deck_index):
        async def callback(interaction: discord.Interaction):
            deck_key = f"deck{deck_index}"
            self.current_deck = f"deck{deck_index}"
            self.show_deck_controls()

            # Récupère les infos du deck
            deck_data = self.decks.get(deck_key, {"name": f"Deck {deck_index}", "cards": {}})
            deck_name = deck_data.get("name", f"Deck {deck_index}")
            deck_cards = deck_data.get("cards", {})

            # Construction de la description avec emoji + nom
            if deck_cards:
                description_lines = [
                    f"{pos} → {card['emoji']} {card['name']}"
                    for pos, card in sorted(deck_cards.items(), key=lambda x: int(x[0]))
                ]
                description = "\n".join(description_lines)
            else:
                description = "❌ Ce deck est **vide**."

            embed = discord.Embed(
                title=f"📦 Contenu du Deck : {deck_name}",
                description=description,
                color=discord.Color.blurple()
            )

            # Affiche les boutons de contrôle (retour / ajouter / retirer / renommer)
            self.show_deck_controls()
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    def show_deck_controls(self):
        self.clear_items()

        deck = self.decks.get(self.current_deck)
        deck_cards = deck.get("cards", {}) if deck else {}

        # Bouton retour
        back_button = Button(
            label="⬅️ Retour",
            style=discord.ButtonStyle.gray
        )
        back_button.callback = self.go_back
        self.add_item(back_button)

        # Bouton Ajouter
        add_button = Button(
            label="➕ Ajouter",
            style=discord.ButtonStyle.green,
            disabled=not self.can_edit
        )
        add_button.callback = self.add_card
        self.add_item(add_button)

        # Bouton Supprimer
        remove_button = Button(
            label="➖ Retirer",
            style=discord.ButtonStyle.red,
            disabled=(not self.can_edit or not deck_cards)
        )
        remove_button.callback = self.remove_card
        self.add_item(remove_button)

        # Bouton Renommer
        rename_button = Button(
            label="✏️ Renommer",
            style=discord.ButtonStyle.blurple,
            disabled=not self.can_edit
        )
        rename_button.callback = self.rename_deck
        self.add_item(rename_button)

    async def rename_deck(self, interaction: discord.Interaction):
        # Affiche un modal pour entrer le nouveau nom
        modal = RenameDeckModal(view=self, deck_key=self.current_deck)
        await interaction.response.send_modal(modal)

    async def go_back(self, interaction: discord.Interaction):
        self.show_deck_list()

        embed = discord.Embed(
            title="🎴 Liste des decks",
            description="Clique sur un bouton pour afficher un deck.",
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def add_card(self, interaction: discord.Interaction):
        cards = load.load_cards  # ton JSON complet des cartes

        modal = AddCardModal(
            view=self,
            deck_key=self.current_deck,
            cards=cards
        )
        await interaction.response.send_modal(modal)

    async def remove_card(self, interaction: discord.Interaction):
        modal = RemoveCardModal(view=self, deck_key=self.current_deck)
        await interaction.response.send_modal(modal)

class Decks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["deck", "d"]) # <--------------------------------------------------- COMMANDE DECKS
    async def decks(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        user_id = str(user.id)
        player_decks = load.player_decks

        player_decks = await guards.checkDecks(user_id, player_decks)
        decks = player_decks[user_id]

        embed = discord.Embed(
            title=f"🎴 Decks de {user.display_name}",
            description="Clique sur un bouton pour afficher un deck.",
            color=discord.Color.blurple()
        )
        load.save_decks()
        can_edit = (ctx.author.id == user.id)

        view = DeckView(ctx, decks, can_edit)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Decks(bot)) # Ajoute le cog Decks au bot