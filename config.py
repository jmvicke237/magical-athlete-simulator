# config.py

from characters.base_character import Character

# Import all your character classes (your list is correct)
from characters.hugebaby import HugeBaby
from characters.cheerleader import Cheerleader
from characters.magician import Magician
from characters.gunk import Gunk
from characters.duelist import Duelist
from characters.legs import Legs
from characters.mouth import MOUTH
from characters.leaptoad import Leaptoad
from characters.romantic import Romantic
from characters.lackey import Lackey
from characters.inchworm import Inchworm
from characters.centaur import Centaur
from characters.partyanimal import PartyAnimal
from characters.flipflop import FlipFlop
from characters.skipper import Skipper
from characters.genius import Genius
from characters.suckerfish import Suckerfish
from characters.hypnotist import Hypnotist
from characters.banana import Banana
from characters.heckler import Heckler
from characters.babayaga import BabaYaga
from characters.mastermind import Mastermind
from characters.alchemist import Alchemist
from characters.dummy import Dummy
from characters.scoocher import Scoocher
from characters.dicemonger import Dicemonger
from characters.hare import Hare
from characters.coach import Coach
from characters.blimp import Blimp
from characters.rocketscientist import RocketScientist
from characters.loveableloser import LoveableLoser
from characters.thirdwheel import ThirdWheel
from characters.sisyphus import Sisyphus
from characters.stickler import Stickler

# V2 characters
from characters.dummy2 import Dummy2
from characters.overtaker import Overtaker
from characters.kingtripper import Kingtripper
from characters.diva import Diva
from characters.mrdiceguy import MrDiceGuy
from characters.normalharry import NormalHarry
from characters.lesaboteur import LeSaboteur
from characters.nepobaby import NepoBaby
from characters.spoilsport import Spoilsport
from characters.cheatah import Cheatah
from characters.hogknight import HogKnight
from characters.speeddemon import SpeedDemon
from characters.partypooper import PartyPooper
from characters.blunderdog import Blunderdog
from characters.thehose import TheHose
from characters.mole import Mole
from characters.stunner import Stunner
from characters.stepdad import Stepdad
from characters.null import Null
from characters.hopfrog import Hopfrog
from characters.gloth import Gloth
from characters.soulmate import Soulmate
from characters.tail import Tail
from characters.kraken import Kraken
from characters.critic import Critic
from characters.showoff import ShowOff
from characters.streaker import Streaker
from characters.hotel import Hotel
from characters.penguin import Penguin
from characters.nemesis import Nemesis
from characters.magicalathlete import MagicalAthlete
from characters.icarus import Icarus
from characters.doppelgangster import Doppelgangster

character_abilities = {
    "HugeBaby": HugeBaby,
    "Cheerleader": Cheerleader,
    "Magician": Magician,
    "Gunk": Gunk,
    "Duelist": Duelist,
    "Legs": Legs,
    "MOUTH": MOUTH,
    "Leaptoad": Leaptoad,
    "Romantic": Romantic,
    "Lackey": Lackey,
    "Inchworm": Inchworm,
    "Centaur": Centaur,
    "PartyAnimal": PartyAnimal,
    "FlipFlop": FlipFlop,
    "Skipper": Skipper,
    "Genius": Genius,
    "Suckerfish": Suckerfish,
    "Hypnotist": Hypnotist,
    "Banana": Banana,
    "Heckler": Heckler,
    "BabaYaga": BabaYaga,
    "Mastermind": Mastermind,
    "Alchemist": Alchemist,
    "Dummy": Dummy,
    "Scoocher": Scoocher,
    "Dicemonger": Dicemonger,
    "Hare": Hare,
    "Coach": Coach,
    "Blimp": Blimp,
    "RocketScientist": RocketScientist,
    "LovableLoser": LoveableLoser,
    "ThirdWheel": ThirdWheel,
    "Sisyphus": Sisyphus,
    "Stickler": Stickler,
    "Dummy2": Dummy2,
    "Overtaker": Overtaker,
    "Kingtripper": Kingtripper,
    "Diva": Diva,
    "MrDiceGuy": MrDiceGuy,
    "NormalHarry": NormalHarry,
    "LeSaboteur": LeSaboteur,
    "NepoBaby": NepoBaby,
    "Spoilsport": Spoilsport,
    "Cheatah": Cheatah,
    "HogKnight": HogKnight,
    "SpeedDemon": SpeedDemon,
    "PartyPooper": PartyPooper,
    "Blunderdog": Blunderdog,
    "TheHose": TheHose,
    "Mole": Mole,
    "Stunner": Stunner,
    "Stepdad": Stepdad,
    "Null": Null,
    "Hopfrog": Hopfrog,
    "Gloth": Gloth,
    "Soulmate": Soulmate,
    "Tail": Tail,
    "Kraken": Kraken,
    "Critic": Critic,
    "ShowOff": ShowOff,
    "Streaker": Streaker,
    "Hotel": Hotel,
    "Penguin": Penguin,
    "Nemesis": Nemesis,
    "MagicalAthlete": MagicalAthlete,
    "Icarus": Icarus,
    "Doppelgangster": Doppelgangster,
}

# Edition options for the frontend toggle. Each character class declares its
# EDITION on the class itself (default "v1" via Character base).
EDITIONS = ["V1", "V2", "All"]
DEFAULT_EDITION = "V2"


def get_characters_by_edition(edition):
    """Return a filtered {name: class} dict for the given edition.

    edition: "V1", "V2", or "All" (case-insensitive). Unknown values return all.
    """
    if edition is None:
        return dict(character_abilities)
    key = edition.lower()
    if key == "all":
        return dict(character_abilities)
    return {
        name: cls for name, cls in character_abilities.items()
        if getattr(cls, "EDITION", "v1") == key
    }


# Game-wide constants
BOARD_LENGTH = 30
MAX_TURNS = 50
CORNER_POSITION = 15  # Updated to match new board layout

# Board options
BOARD_TYPES = ["Mild", "Wild", "Sportals", "Twists", "Random"]
DEFAULT_BOARD_TYPE = "Mild"