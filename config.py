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
from characters.kingslayer import Kingslayer
from characters.caboose import Caboose
from characters.diceman import Diceman
from characters.weremouth import Weremouth
from characters.stinkeye import StinkEye
from characters.silverspoon import SilverSpoon
from characters.spoilsport import Spoilsport
from characters.cheatah import Cheatah
from characters.hogknight import HogKnight
from characters.prometheus import Prometheus
from characters.partypooper import PartyPooper
from characters.blunderdog import Blunderdog
from characters.spitball import SpitBall
from characters.mole import Mole
from characters.stunner import Stunner
from characters.stepdad import Stepdad
from characters.antimagicalathlete import AntimagicalAthlete

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
    "Kingslayer": Kingslayer,
    "Caboose": Caboose,
    "Diceman": Diceman,
    "Weremouth": Weremouth,
    "StinkEye": StinkEye,
    "SilverSpoon": SilverSpoon,
    "Spoilsport": Spoilsport,
    "Cheatah": Cheatah,
    "HogKnight": HogKnight,
    "Prometheus": Prometheus,
    "PartyPooper": PartyPooper,
    "Blunderdog": Blunderdog,
    "SpitBall": SpitBall,
    "Mole": Mole,
    "Stunner": Stunner,
    "Stepdad": Stepdad,
    "AntimagicalAthlete": AntimagicalAthlete,
}

# Edition options for the frontend toggle. Each character class declares its
# EDITION on the class itself (default "v1" via Character base).
EDITIONS = ["V1", "V2", "All"]
DEFAULT_EDITION = "V1"


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
BOARD_TYPES = ["Mild", "Wild", "Random"]
DEFAULT_BOARD_TYPE = "Mild"