import json; import os
from utils import config;

INVENTORY_FILE = config.INVENTORY_FILE
CARDS_FILE = config.CARDS_FILE
STATS_FILE = config.STATS_FILE
PITY_FILE = config.PITY_FILE
DECKS_FILE = config.DECKS_FILE

def load_json(file_path, default=None):  # Charge les données JSON
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"⚠️ Fichier JSON corrompu : {file_path}, réinitialisation...")
    return default if default is not None else {}

def save_json(file_path, data): # Sauvegarde les donnés JSON
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def load_cards_stats(): # Charge les stats des cartes
    return load_json(STATS_FILE, default={})

def load_pity(): # Charge les pity
    return load_json(PITY_FILE, default={})

def save_pity(): # Sauvegarde les pity
    save_json(PITY_FILE, player_pity)

def load_inventory(): # Charge les inventaires
    return load_json(INVENTORY_FILE, default={})

def save_inventory(): # Sauvegarde les inventaires
    save_json(INVENTORY_FILE, player_inventory)

def load_cards(): # Charge les cartes
    return load_json(CARDS_FILE, default={})

def load_card_probabilities(): # Charges les probas des cartes
    cards = load_cards()
    probabilities = {rarity: info.get("probability", 0) for rarity, info in cards.items()}
    return probabilities

def load_decks(): # Charge les decks
    return load_json(DECKS_FILE, default={})

def save_decks(): # Sauvegarde les decks
    save_json(DECKS_FILE, player_decks)

# Charger les données au démarrage
card_stats = load_cards_stats()
cards = load_cards()
player_pity = load_pity()
player_inventory = load_inventory()
player_decks = load_decks()
config_probabilities = load_card_probabilities()