# partyanimal.py

from .base_character import Character

class PartyAnimal(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.number_of_sharers = 0
        self.used_ability = False
        
    def pre_move_action(self, game, play_by_play_lines):
        """All other racers move one space towards the Party Animal.
        The Party Animal gets +1 to its Main Move for each other racer on its Space.
        """
        # Move all other racers 1 space towards the Party Animal
        self.number_of_sharers = 0
        self.used_ability = False
        for player in game.players:
            if player != self and not player.finished and player not in game.eliminated_players:
                if player.position < self.position:
                    player.move(game, play_by_play_lines, 1) #Move one towards partyanimal, forward.
                    self.used_ability = True
                elif player.position > self.position:
                    player.move(game, play_by_play_lines, -1) #Move them one backwards
                    self.used_ability = True
        self.number_of_sharers = len(self.check_for_share_space(game))
        if self.number_of_sharers > 0:
            self.used_ability = True
        if self.used_ability:
            game.trigger_scoocher(play_by_play_lines)

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Check the number of people at the party to give a bonus."""
        if other_player == self:
            modified_roll = roll + self.number_of_sharers
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) gets +{self.number_of_sharers} to their roll for having {self.number_of_sharers} racers. Roll: {roll} -> {modified_roll}"
            )
            return modified_roll
        return roll