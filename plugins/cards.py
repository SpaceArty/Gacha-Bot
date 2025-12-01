import discord; from discord.ext import commands
from discord.ui import View, Button
from utils import load, guards, config

RARITY_EMOJIS = config.RARITY_EMOJIS

# Affichage d'une carte
class InfoView(guards.AuthorOnlyView):
    def __init__(self, ctx, embeds):
        super().__init__(owner=ctx.author)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)

        # Initialisation des boutons
        self.previous_button = Button(label="Page précédente", style=discord.ButtonStyle.green)
        self.previous_button.callback = self.previous_page
        self.next_button = Button(label="Page suivante", style=discord.ButtonStyle.green)
        self.next_button.callback = self.next_page

        # Ajout des boutons à la vue
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

        # Mise à jour des boutons
        self.update_buttons()

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons() # Mise à jour des boutons avant l'envoi du message

            # Mise à jour du message avec l'embed correspondant à la page
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons() # Mise à jour des boutons avant l'envoi du message

            # Mise à jour du message avec l'embed correspondant à la page
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

class Cards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["i"]) # <----------------------------------------------------------- COMMANDE INFO
    async def info(self, ctx, card_name: str = None):
        if card_name is None: # Vérifie que les arguments nécessaires sont présents
            await ctx.send(f"{ctx.author.mention}, veuillez spécifier le nom d'une carte. Usage : `!info [nom de la carte]`." )
            return

        cards = load.cards
        card_stats = load.card_stats

        found = await guards.checkCard(ctx, card_name, cards) # Vérifie la carte
        if found is None: return
        real_name, rarity, image_url, color = found
        embeds = []

        embed1 = discord.Embed(
            title=f"📜 Informations sur la carte : {real_name}",
            description=f"**Rareté :** {rarity}",
            color=discord.Color(int(color.lstrip('#'), 16)) # Couleur définie ici
        )
        embed1.set_image(url=image_url)
        embeds.append(embed1)

        if real_name in card_stats:
            stats = card_stats[real_name]
            embed2 = discord.Embed(
                title=f"📊 Statistiques de la carte : {real_name}",
                description=f"**Description :** {stats['description'] or 'Aucune'}\n"
                            f"**Passif :** {stats['passif'] or 'Aucun'}\n"
                            f"**Attaque :** {stats['attaque']}\n"
                            f"**Défense :** {stats['defense']}",
                color=discord.Color(int(color.lstrip('#'), 16)) # Utilisation de la même couleur
            )
            embeds.append(embed2)

        view = InfoView(ctx, embeds)
        message = await ctx.send(embed=embeds[0], view=view)
        view.update_buttons()

    @commands.command(aliases=["cl"]) # <---------------------------------------------------------- COMMANDE CARDLIST
    async def cardlist(self, ctx):
        cards = load.cards
        embed = discord.Embed(title="📜 Liste des cartes disponibles", color=discord.Color.gold())

        for rarity, info in cards.items():
            emoji = RARITY_EMOJIS.get(rarity, "❓")
            card_names = ", ".join(info["cards"].keys()) if info["cards"] else "Aucune carte"
            embed.add_field(name=f"{emoji} {rarity}", value=card_names, inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["inv"])  # <-------------------------------------------------------- COMMANDE INVENTAIRE
    async def inventory(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        user_id = str(user.id)
        player_inventory = load.player_inventory
        cards = load.cards

        player_inventory = await guards.checkInventory(user_id, player_inventory) # Vérifie l'inventaire
        inventory = player_inventory[user_id]  # L'inventaire de l'user

        if len(inventory) == 0:
            await ctx.send(f"{ctx.author.mention}, ton inventaire est vide !")
            return

        for card_name, data in player_inventory[user_id].items():
            if not isinstance(data, dict) or "rarity" not in data or "count" not in data or "image" not in data:
                await ctx.send(f"{user.mention}, l'inventaire est corrompu !")
                return
        sorted_inventory = sorted(player_inventory[user_id].items(), key=lambda x: list(cards.keys()).index(x[1]["rarity"]))

        cards_per_page = 20 # <-------------------------------------------------------------------- CARTES PAR PAGES
        total_pages = (len(sorted_inventory) + cards_per_page - 1) // cards_per_page

        def create_embed(page):
            start_index = (page - 1) * cards_per_page
            end_index = min(page * cards_per_page, len(sorted_inventory))
            page_inventory = sorted_inventory[start_index:end_index]

            highest_rarity = page_inventory[-1][1]["rarity"] if page_inventory else "Common"
            embed_color = cards[highest_rarity]["color"]

            # Convertir la couleur hexadécimale en discord.Colour
            if embed_color.startswith("#"):
                embed_color = discord.Colour(int(embed_color[1:], 16)) # Conversion en int puis en discord.Colour
            
            embed = discord.Embed(title=f"📜 Inventaire de {user.name} - Page {page}/{total_pages}", color=embed_color)
            
            for name, data in page_inventory:
                embed.add_field(name=f"🔹 {name} ({data['rarity']})", value=f"Quantité : x{data['count']}", inline=True)
            return embed

        # Affichage de l'inventaire
        class PaginationButtons(guards.AuthorOnlyView):
            def __init__(self, ctx, user, total_pages, current_page, embed):
                super().__init__(owner=ctx.author)
                self.user = user
                self.total_pages = total_pages
                self.current_page = current_page
                self.embed = embed

                self.previous_button = Button(label="Page précédente", style=discord.ButtonStyle.green)
                self.previous_button.callback = self.previous_page
                self.next_button = Button(label="Page suivante", style=discord.ButtonStyle.green)
                self.next_button.callback = self.next_page

                self.add_item(self.previous_button)
                self.add_item(self.next_button)
                self.update_buttons()

            async def previous_page(self, interaction: discord.Interaction):
                if self.current_page > 1:
                    self.current_page -= 1
                    new_embed = create_embed(self.current_page)
                    self.embed = new_embed
                    self.update_buttons()
                    await interaction.response.edit_message(embed=new_embed, view=self)

            async def next_page(self, interaction: discord.Interaction):
                if self.current_page < self.total_pages:
                    self.current_page += 1
                    new_embed = create_embed(self.current_page)
                    self.embed = new_embed
                    self.update_buttons()
                    await interaction.response.edit_message(embed=new_embed, view=self)

            def update_buttons(self):
                self.previous_button.disabled = self.current_page == 1
                self.next_button.disabled = self.current_page == self.total_pages

        embed = create_embed(1)
        view = PaginationButtons(ctx, ctx.author, total_pages, 1, embed)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Cards(bot)) # Ajoute le cog Cards au bot