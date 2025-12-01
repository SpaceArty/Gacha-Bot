from discord.ext import commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        # Ne pas override un error handler local
        if hasattr(ctx.command, "on_error"):
            return

        # Si erreur encapsulée → on récupère la vraie
        error = getattr(error, "original", error)

        # === GESTION DES ERREURS ===

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"{ctx.author.mention}, un argument est invalide.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author.mention}, il manque des arguments.")
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{ctx.author.mention}, tu n’as pas la permission.")
            return

        if isinstance(error, commands.CommandNotFound):
            return  # ignore simplement

        # Erreur inattendue → message + log
        await ctx.send(f"❌ Une erreur est survenue : `{error}`")
        raise error


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot)) # Ajoute le cog Error au bot