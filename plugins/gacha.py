import discord; from discord.ui import View, Button
from discord.ext import commands; import random
from utils import load, guards

cards = load.load_cards()

# Affichage du tirage
class PullView(guards.AuthorOnlyView):
    def __init__(self, ctx, user):
        super().__init__(owner=ctx.author)
        self.user = user # Stocke l'auteur du message

    async def create_pull(self, interaction, pulls, forced_rarity=None):
        if interaction.user != self.user:
            await interaction.response.send_message("Tu ne peux pas utiliser ces boutons !", ephemeral=True)
            return
        await self.handle_pull(interaction, pulls, forced_rarity)

    @discord.ui.button(label="1x Pull", style=discord.ButtonStyle.primary)
    async def one_pull(self, interaction: discord.Interaction, button: Button):
        await self.create_pull(interaction, pulls=1)

    @discord.ui.button(label="10x Pull", style=discord.ButtonStyle.green)
    async def ten_pull(self, interaction: discord.Interaction, button: Button):
        await self.create_pull(interaction, pulls=10)

    @discord.ui.button(label="??? Pull", style=discord.ButtonStyle.red)
    async def zero_pull(self, interaction: discord.Interaction, button: Button):
        await self.create_pull(interaction, pulls=1, forced_rarity="Trash")

    async def handle_pull(self, interaction, pulls, forced_rarity=None):
        results = []
        user_id = str(self.user.id)
        player_inventory = load.player_inventory

        for _ in range(pulls):
            # Si on veut forcer une rareté spécifique, on l'utilise
            if forced_rarity:
                chosen_rarity = forced_rarity
            else:
                rarity, card_name, image_url, color = await pull_card(user_id)
                chosen_rarity = rarity

            # Choisir une carte au hasard parmi les cartes de la rareté tirée
            chosen_card = random.choice(list(cards[chosen_rarity]["cards"].keys()))

            # Initialiser l'inventaire de l'utilisateur si nécessaire
            if user_id not in player_inventory:
                player_inventory[user_id] = {}

            # Ajouter ou mettre à jour la carte dans l'inventaire
            if chosen_card in player_inventory[user_id]:
                player_inventory[user_id][chosen_card]["count"] += 1
            else:
                player_inventory[user_id][chosen_card] = {"rarity": chosen_rarity, "count": 1, "image": cards[chosen_rarity]["cards"][chosen_card]}
            results.append((chosen_rarity, chosen_card, cards[chosen_rarity]["cards"][chosen_card], cards[chosen_rarity]["color"]))
        load.save_inventory()

        # Liste des raretés par ordre de valeur
        rarity_order = ["Trash", "Common", "Rare", "Epic", "Legendary", "Goat", "Dieu"]
        highest_rarity_card = max(results, key=lambda x: rarity_order.index(x[0]))

        # Créer un embed pour afficher les résultats
        embed = discord.Embed(title=f"{self.user.name} a tiré {pulls} carte(s) !", color=discord.Color(int(highest_rarity_card[3].lstrip('#'), 16)))

        # Ajouter toutes les cartes tirées dans l'embed
        for rarity, card_name, image_url, color in results:
            embed.add_field(name=f"**{card_name}** ({rarity})", value="\u200b", inline=False) # Utiliser un champ vide pour espacer
            embed.set_image(url=image_url) # Afficher l'image sous chaque carte tirée (si nécessaire)

        # Afficher l'image de la carte la plus rare
        embed.set_image(url=highest_rarity_card[2])

        # Répondre avec l'embed et supprimer les boutons
        await interaction.response.edit_message(embed=embed, view=None)
        
# Tirage des cartes
async def pull_card(user_id):
    global player_pity
    player_pity = load.player_pity

    player_pity = await guards.checkPity(user_id, player_pity) # Vérifie que la pity existe
    pity_bonus = player_pity[user_id] * 0.003 # <-------------------------------------------------- PITY INCREASE

    # Appliquer le pity sur les probabilités
    adjusted_probabilities = {}
    total_weight = 0

    for rarity, info in cards.items():
        base_prob = info["probability"]

        if rarity == "Goat":
            base_prob += pity_bonus # Augmente la probabilité du Goat
        if rarity == "Trash":
            base_prob -= pity_bonus # Diminue celle du Déchet

        adjusted_probabilities[rarity] = base_prob
        total_weight += base_prob # Calculer le poids total

    # Normalisation pour garder un total de 100%
    for rarity in adjusted_probabilities:
        adjusted_probabilities[rarity] = (adjusted_probabilities[rarity] / total_weight) * 100

    # Choisir une rareté selon les nouvelles probabilités
    rarity_choices = list(adjusted_probabilities.keys())
    rarity_weights = list(adjusted_probabilities.values())

    chosen_rarity = random.choices(rarity_choices, weights=rarity_weights, k=1)[0]
    chosen_card = random.choice(list(cards[chosen_rarity]["cards"].keys()))

    # Reset du pity si un Légendaire est obtenu
    if chosen_rarity == "Goat":
        player_pity[user_id] = 0
    else:
        player_pity[user_id] += 1 # Augmente le pity si pas de Goat
    load.save_pity() # Sauvegarde le pity

    return chosen_rarity, chosen_card, cards[chosen_rarity]["cards"][chosen_card], cards[chosen_rarity]["color"]

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["p",""]) # <-------------------------------------------------------- COMMANDE PULL
    async def pull(self, ctx):
        embed = discord.Embed(title="🎲 Choisis ton tirage :", description="Clique sur un bouton pour tirer une carte !", color=discord.Color.blue())
        view = PullView(ctx, ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["pt"]) # <------------------------------------------------------------------------ COMMANDE PITY
    async def pity(self, ctx, user: discord.Member = None):
        config_probabilities = load.config_probabilities
        player_pity = load.player_pity

        # Si aucun utilisateur n'est mentionné, utiliser l'auteur du message
        user = user or ctx.author
        user_id = str(user.id)
        load.load_pity()

        player_pity = await guards.checkPity(user_id, player_pity) # Vérifie que la pity existe

        pity = player_pity[user_id]
        pity_increase = 0.003 # Augmentation de la probabilité

        # Calcul des nouvelles probabilités
        goat_probability = config_probabilities["Goat"] + pity * pity_increase
        trash_probability = config_probabilities["Trash"] - pity * pity_increase

        # Vérification des limites
        goat_probability = min(goat_probability, 100)
        trash_probability = max(trash_probability, 0)

        other_probabilities = {k: v for k, v in config_probabilities.items() if k not in ["Goat", "Trash"]}

        # Embed de réponse
        embed = discord.Embed(title=f"Taux de drop et Pity de {user.name}", color=discord.Color.blue())
        embed.add_field(name="🎯 **Pity actuel**", value=f"{pity}", inline=False)
        embed.add_field(name="📊 **Probabilité de carte Goat**", value=f"{goat_probability}%", inline=False)
        embed.add_field(name="📉 **Probabilité de déchet**", value=f"{trash_probability}%", inline=False)

        for rarity, prob in other_probabilities.items():
            embed.add_field(name=f"📦 **{rarity}**", value=f"{prob}%", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gacha(bot)) # Ajoute le cog Gacha au bot