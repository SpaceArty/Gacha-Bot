import discord; import difflib
from utils import config, load

AUTHORIZED_USERS = config.AUTHORIZED_USERS

async def checkAdmin(ctx): # Vérifie si l'utilisateur donné est admin
    if ctx.author.id not in AUTHORIZED_USERS:
        await ctx.send(f"{ctx.author.mention}, tu n'as pas la permission d'utiliser cette commande.",ephemeral=True)
        return False
    return True

async def checkCard(ctx, card_name, cards): # Vérifie si le nom de carte existe et la renvois
    raw_input = card_name.strip().strip('"')
    input_norm = normalize(raw_input)
    name_mapping = {}   # normalized → (real_name, rarity, image, color)

    for rarity, info in cards.items():
        color = info["color"]
        for real_name, image_url in info["cards"].items():
            name_mapping[normalize(real_name)] = (real_name, rarity, image_url, color)

    if input_norm in name_mapping:
        return name_mapping[input_norm]

    normalized_names = list(name_mapping.keys())
    matches = difflib.get_close_matches(input_norm, normalized_names, n=1, cutoff=0.6)

    if matches:
        return name_mapping[matches[0]]

    await ctx.send(f"{ctx.author.mention}, la carte **{card_name}** n'existe pas.", ephemeral=True)
    return None

async def checkInventory(user_id, player_inventory): # Vérifie si l'inventaire existe, le crée sinon
    user_id = str(user_id)
    if user_id not in player_inventory:
        player_inventory[user_id] = {}
        load.save_inventory()
    return player_inventory

async def checkDecks(user_id, player_decks): # Vérifie si l'inventaire existe, le crée sinon
    user_id = str(user_id)
    if user_id not in player_decks:
        # Crée 6 decks avec ID 1 à 6
        player_decks[user_id] = {
            f"deck{i}": {"id": i, "name": f"Deck {i}", "cards": {}}
            for i in range(1, 7)
        }
        load.save_decks()
    return player_decks

async def checkDeckLegal(ctx, deck: dict):
    if not isinstance(deck, dict): # Le deck doit être un dict
        return False

    if len(deck) != 6: # Vérifier que le deck contient exactement 6 entrées
        return False

    for i in range(1, 6 + 1): # Vérifier les positions 1 → 6
        pos = str(i)

        if pos not in deck:
            return False
        card = deck[pos]

        # Vérifier que chaque case contient bien une carte
        if not isinstance(card, dict) or "name" not in card:
            return False
    return True

async def checkPity(user_id, player_pity): # Vérifie si la pity existe, la crée sinon
    if user_id not in player_pity:
        player_pity[user_id] = 0
        load.save_pity()
    return player_pity

class AuthorOnlyView(discord.ui.View): # View par défaut pour vérifier les interactions
    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.owner:
            await interaction.response.send_message("❌ Seul l'utilisateur ayant exécuté la commande peut interagir avec les boutons !", ephemeral=True)
            return False
        return True
    
def normalize(s: str) -> str: # Normalise un String
    return " ".join(s.strip().lower().split())