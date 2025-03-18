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
from characters.boogeyman import Boogeyman
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
from characters.clowncar import ClownCar
from characters.egg import Egg
from characters.loveableloser import LoveableLoser
from characters.twin import Twin
from characters.thirdwheel import ThirdWheel

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
    "Boogeyman": Boogeyman,
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
    "ClownCar": ClownCar,
    "Egg": Egg,
    "LovableLoser": LoveableLoser,
    "Twin": Twin,
    "ThirdWheel": ThirdWheel
}

# Game-wide constants
BOARD_LENGTH = 30
MAX_TURNS = 50
CORNER_POSITION = 20