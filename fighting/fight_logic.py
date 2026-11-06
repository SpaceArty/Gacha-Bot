import discord; import random
from discord.ui import View, Button
from discord.ext import commands
from utils import load, guards, config

class Card: # La classe carte
    def __init__(self, nom, HP, attaque, defense, esquive, precision, id, effets=None, dead=False):
        self.nom = nom
        self.HP = HP
        self.attaque = attaque
        self.defense = defense
        self.esquive = esquive
        self.precision = precision
        self.id = id
        self.effets = effets if effets is not None else []
        self.dead = dead

class Fight_Logic():
    async def start_fight(self, player1: discord.Member, player2: discord.Member, deck1: str, deck2: str):
        decks = load.load_decks()
        cards_stats = load.load_cards_stats()
        
        user1_id = str(player1.id)
        user2_id = str(player2.id)

        # Récupérer les decks complets
        deck1_data = decks[user1_id][deck1]
        deck2_data = decks[user2_id][deck2]
        
        # Extraire les noms des cartes depuis la clé 'cards'
        deck1_cards = deck1_data['cards']
        deck2_cards = deck2_data['cards']

        self.deck1 = []  # Créer les objets Card pour le deck 1
        for card_id, card_info in deck1_cards.items():
            card_name = card_info['name']
            if card_name in cards_stats:
                card_data = cards_stats[card_name]
                card = Card(
                    nom=card_name,
                    HP=100,
                    precision=100,
                    esquive=100,
                    attaque=card_data["attaque"],
                    defense=card_data["defense"],
                    id=card_data["ID"],
                    dead=False
                )
                self.deck1.append(card)

        self.deck2 = []  # Créer les objets Card pour le deck 2
        for card_id, card_info in deck2_cards.items():
            card_name = card_info['name']
            if card_name in cards_stats:
                card_data = cards_stats[card_name]
                card = Card(
                    nom=card_name,
                    HP=100,
                    precision=100,
                    esquive=100,
                    attaque=card_data["attaque"],
                    defense=card_data["defense"],
                    id=card_data["ID"],
                    dead=False
                )
                self.deck2.append(card)
        return self.deck1, self.deck2
    
    def is_card_dead(self, card: Card) -> bool:
        return card.dead

    def are_all_cards_dead(self, deck: list[Card]) -> bool:
        return all(card.dead for card in deck)

    def attack(self, attacker, defender):
        # Dégâts de base aléatoire
        base_damage = random.randint(16, 24)

        # Appliquer l'attaque
        damage_with_atk = base_damage * (1 + (attacker.attaque/100))

        # Réduction par défense
        damage_received = damage_with_atk * (1 - (defender.defense/100))

        # Arrondir à l'entier et appliquer sur les PV
        damage_received = int(damage_received)
        defender.HP -= damage_received

        # Vérifier si la carte est morte
        if defender.HP <= 0:
            defender.HP = 0
            defender.dead = True
import discord; import random
from discord.ui import View, Button
from discord.ext import commands
from utils import load, guards, config

class Card: # La classe carte
    def __init__(self, nom, HP, attaque, defense, esquive, precision, id, effets=None, dead=False):
        self.nom = nom
        self.HP = HP
        self.attaque = attaque
        self.defense = defense
        self.esquive = esquive
        self.precision = precision
        self.id = id
        self.effets = effets if effets is not None else []
        self.dead = dead

class Fight_Logic():
    async def start_fight(self, player1: discord.Member, player2: discord.Member, deck1: str, deck2: str):
        decks = load.load_decks()
        cards_stats = load.load_cards_stats()
        
        user1_id = str(player1.id)
        user2_id = str(player2.id)

        # Récupérer les decks complets
        deck1_data = decks[user1_id][deck1]
        deck2_data = decks[user2_id][deck2]
        
        # Extraire les noms des cartes depuis la clé 'cards'
        deck1_cards = deck1_data['cards']
        deck2_cards = deck2_data['cards']

        self.deck1 = []  # Créer les objets Card pour le deck 1
        for card_id, card_info in deck1_cards.items():
            card_name = card_info['name']
            if card_name in cards_stats:
                card_data = cards_stats[card_name]
                card = Card(
                    nom=card_name,
                    HP=100,
                    precision=100,
                    esquive=100,
                    attaque=card_data["attaque"],
                    defense=card_data["defense"],
                    id=card_data["ID"],
                    dead=False
                )
                self.deck1.append(card)

        self.deck2 = []  # Créer les objets Card pour le deck 2
        for card_id, card_info in deck2_cards.items():
            card_name = card_info['name']
            if card_name in cards_stats:
                card_data = cards_stats[card_name]
                card = Card(
                    nom=card_name,
                    HP=100,
                    precision=100,
                    esquive=100,
                    attaque=card_data["attaque"],
                    defense=card_data["defense"],
                    id=card_data["ID"],
                    dead=False
                )
                self.deck2.append(card)
        return self.deck1, self.deck2
    
    def attack(self, attacker, defender):
        # Dégâts de base aléatoire
        base_damage = random.randint(16, 24)

        # Appliquer l'attaque
        damage_with_atk = base_damage * (1 + (attacker.attaque/100))

        # Réduction par défense
        damage_received = damage_with_atk / (defender.defense / 4)

        # Arrondir à l'entier et appliquer sur les PV
        damage_received = int(damage_received)
        defender.HP -= damage_received

        # Vérifier si la carte est morte
        if defender.HP <= 0:
            defender.HP = 0
            defender.dead = True
        return attacker, defender