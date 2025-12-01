import discord; from discord.ext import commands
from discord.ui import View, Button
from utils import load, guards, config

# Affichage du menu help
class PaginationButtons(guards.AuthorOnlyView):
    def __init__(self, ctx, total_pages, current_page, pages):
        super().__init__(owner=ctx.author)
        self.ctx = ctx
        self.total_pages = total_pages
        self.current_page = current_page
        self.pages = pages

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
            new_embed = self.pages[self.current_page - 1] # -1 car l'index des pages commence à 0
            self.update_buttons()
            await interaction.response.edit_message(embed=new_embed, view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages:
            self.current_page += 1
            new_embed = self.pages[self.current_page - 1] # -1 car l'index des pages commence à 0
            self.update_buttons()
            await interaction.response.edit_message(embed=new_embed, view=self)
    
    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == self.total_pages

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["h"]) # <----------------------------------------------------------- COMMANDE HELP
    async def help(self, ctx):
        pages = [
            discord.Embed( # Page 1 - Commandes générales
                title="📜 Liste des commandes",
                description="Voici toutes les commandes disponibles sur le bot.",
                color=discord.Color.blue()
            )
            .add_field(name="🎲 `!pull` ou `!p` ou `!`", value="Tire une carte aléatoire. PS : ! c'est pour les feignasses.", inline=False)
            .add_field(name="📦 `!inventory` ou `!inv` + @Joueur", value="Affiche ton inventaire ou celui d'un autre joueur mentionné.", inline=False)
            .add_field(name="🎯 `!pity` ou `!pt` + @Joueur", value="Affiche ton taux de pity ou celui d'un autre joueur mentionné.", inline=False)
            .add_field(name="🃏 `!cardlist` ou `!cl`", value="Affiche la liste de toutes les cartes disponibles.", inline=False)
            .add_field(name="📜 `!info` ou `!i` + Carte", value="Affiche les détails d'une carte, ainsi que son image correspondante.", inline=False)
            .add_field(name="⚔️ `!fight` ou `!f` + @Joueur", value="Lance un combat contre un autre joueur ou soi-même.", inline=False)
            .set_footer(text="Page 1/2 | Une petite pensée pour Cricri13, dont l'inventaire a été reset."),

            discord.Embed( # Page 2 - Commandes Admin
                title="📜 Commandes Admin",
                description="Commandes réservées aux administrateurs.",
                color=discord.Color.red()
            )
            .add_field(name="🎁 `!give` ou `!g` + @Joueur + Carte + Nombre", value="Commande Admin, donne une carte ou autant que demandé au joueur mentionné.", inline=False)
            .add_field(name="🎯 `!givePity` ou `!gp` + @Joueur + Nombre", value="Commande Admin, change sa pity ou celle d'un autre joueur mentionné.", inline=False)
            .set_footer(text="Page 2/2 | Cricri est vraiment trop bg, c'est pour ça qu'il a secrètement plus de taux de drop.")
        ]

        # Création des boutons de navigation
        view = PaginationButtons(ctx, len(pages), 1, pages)
        await ctx.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(Utils(bot)) # Ajoute le cog Help au bot