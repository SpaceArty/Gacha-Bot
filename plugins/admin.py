import discord; from discord.ext import commands
from utils import load, guards, config

AUTHORIZED_USERS = config.AUTHORIZED_USERS

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["g"])
    async def give(self, ctx, user: discord.Member = None, card_name: str = None, amount: int = 1):
        if user is None: # Vérifie que les arguments nécessaires sont présents
            await ctx.send(f"{ctx.author.mention}, tu dois spécifier un membre pour cette commande.", ephemeral=True)
            return
        if card_name is None:
            await ctx.send(f"{ctx.author.mention}, tu dois spécifier un nom de carte.", ephemeral=True)
            return

        player_inventory = load.player_inventory
        cards = load.cards

        if not await guards.checkAdmin(ctx): return # Vérifie si il est admin

        found = await guards.checkCard(ctx, card_name, cards) # Vérifie la carte
        if found is None: return
        real_name, rarity, image_url, color = found
        user_id = str(user.id)

        player_inventory = await guards.checkInventory(user_id, player_inventory) # Vérifie l'inventaire
        user_inventory = player_inventory[user_id]

        if real_name in user_inventory:
            user_inventory[real_name]["count"] += amount
        else:
            user_inventory[real_name] = {"rarity": rarity, "count": amount, "image": image_url}
        load.save_inventory()

        embed = discord.Embed(
            title=f"🎁 {ctx.author.name} a donné des cartes !",
            description=f"{user.mention} a reçu **{amount}× {real_name}** ({rarity})",
            color=discord.Color(int(color.lstrip('#'), 16))
        )
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["gp"]) # <----------------------------------------------------------  COMMANDE GIVE PITY
    async def givePity(self, ctx, user: discord.Member = None, amount: int = 1):
        if user is None: # Vérifie que les arguments nécessaires sont présents
            await ctx.send(f"{ctx.author.mention}, tu dois spécifier un membre pour cette commande.", ephemeral=True)
            return

        load.load_pity()
        player_pity = load.player_pity  
        user_id = str(user.id)

        if not await guards.checkAdmin(ctx): return # Vérifie si il est admin
        player_pity = await guards.checkPity(user_id, player_pity) # Vérifie la pity

        player_pity[user_id] += amount
        load.save_pity()
        await ctx.send(f"{ctx.author.mention} a donné {amount} pity à {user.mention} !")

async def setup(bot):
    await bot.add_cog(Admin(bot)) # Ajoute le cog Admin au bot