import numpy as np
import random
from game_trainer.games import game, game_node, utility_node

NUM_ACTIONS = 4
NUM_PLAYERS = 2
ACTION_MAP = ['Check', 'Bet', 'Call', 'Fold']
CARDS = ['Q', 'K', 'A']
DEFAULT_ANTE = 1
DEFAULT_BET_SIZE = 1

random.seed(42)

class Utility(utility_node.UtilityNode):
    '''
    Utility at each terminal node
    '''
    def __init__(self, utility):
        self.utility = utility
        super().__init__()
        
    def get_utility(self):
        return self.utility
    
class Clairvoyance(game.Game):
    '''
    Clairvoyance game, as described in Brokos, A. (2019). Play Optimal Poker. p.44.
    '''
    def __init__(self, ante=DEFAULT_ANTE, bet_size=DEFAULT_BET_SIZE):
        super().__init__(NUM_ACTIONS, NUM_PLAYERS, ACTION_MAP)
        self.cards = CARDS
        self.ante = ante
        self.bet_size = bet_size
       
    def is_chance_node(self, history):
        '''
        Returns true if chance defines the action at this game state
        '''
        return len(history) <= 1 #cards are dealt
    
    def is_terminal_node(self, history):
        '''
        Returns true if the state is terminal
        '''
        if len(history) <= 2:
            return False

        if len(history) == 5:
            return True
        
        if history[-2][1] == 1: # The second to last move was a bet
            return True

        if history[-2][1] == 0 and history[-1][1] == 0: # Two checks in a row
            return True

        return False

    def handle_chance(self, history, sample=False):
        '''
        A helper function that handles behavior at a given chance node. Returns a list of chance outcomes and a list of
        probabilities corresponding to each of those outcomes. If sample is false, all possible actions at that chance
        node are returned, otherwise a user-defined subset is returned.
        '''
        chance_outcomes = []
        chance_probs = []

        player1_card = 'K' # always deal king to player 1

        for card in CARDS:
            if card != player1_card:
                chance_outcomes.append(card)
                chance_probs.append(1 / 2)
                
        return chance_outcomes, chance_probs

    def calculate_pot(self, history):
        '''
        A helper function that calculates the current pot size
        '''
        pot = 2 * self.ante

        if any(action[1] == 2 for action in history):
            pot += 2 * self.bet_size

        return pot
    
    def get_terminal_utility(self, history, pot):
        '''
        Returns the utility at a terminal node for the player who just acted.
        '''
        player = self.get_player(history)
        opp_player = (player + 1) % 2

        player_card = history[0 + player][1]
        opp_player_card = history[0 + opp_player][1]

        if history[-1][1] == 3: # The last player folded
            if history[-1][0] == player:
                return -pot

            return pot

        else:
            if CARDS.index(player_card) > CARDS.index(opp_player_card):
                return pot
            else:
                return -pot
            
    def get_available_actions(self, history):
        '''
        Returns the actions available to a given player at the current state. The actions should be represented as a
        NumPy array.
        '''
        if len(history) == 2: # Cards have been dealt
            actions = np.array([0, 1])

        elif len(history) == 3: # The first player has acted
            if history[-1][1] == 0: # The last action was a check
                actions = np.array([0, 1])

            else: # The last action was a bet
                actions = np.array([2, 3])

        else: # The last action was a bet
            actions = np.array([2, 3])

        return actions

    def get_player(self, history):
        '''
        Returns the identifier of the player who acts in this state.
        '''
        if len(history) == 0:
            return 0

        last_turn = history[-1]

        if last_turn[0] == 0:
            return 1

        return 0

    def get_infoset_key(self, history):
        '''
        Returns a string representation of the game history to be used as a unique information set key.
        '''
        player = self.get_player(history)
        card = history[player][1]
        infoset = card

        for action in history:
            if action[0] != 'r':
                infoset += '-' + str(action[1])

        return infoset

    def build_game_tree(self, history=[]):
        '''
        Recursively builds a game tree consisting of GameNode objects.
        '''
        player = self.get_player(history)
        is_chance_node = self.is_chance_node(history)
        is_terminal_node = self.is_terminal_node(history)

        if is_terminal_node:
            pot = self.calculate_pot(history)
            terminal_utility = self.get_terminal_utility(history, pot)
            utility_node = Utility(terminal_utility)

            return game_node.GameNode(history, player, is_terminal_node=True, terminal_utility=utility_node)

        elif is_chance_node:
            chance_outcomes, chance_probs = self.handle_chance(history)
            next_nodes = []
            history = [('r', 'K')] # deal to player 1
            for outcome in chance_outcomes:
                next_history = history + [('r', outcome)]
                next_nodes.append(self.build_game_tree(history=next_history))

            return game_node.GameNode(history, player, next_nodes, is_chance_node=True, chance_outcomes=chance_outcomes, chance_probs=chance_probs)

        else:
            available_actions = self.get_available_actions(history)
            next_nodes = []

            for action in available_actions:
                next_history = history + [(player, action)]
                next_nodes.append(self.build_game_tree(history=next_history))

            return game_node.GameNode(history, player, next_nodes, available_actions)
        
    def get_metrics(self, infosets, expected_game_value, iteration):
        """
        Extracts relevant metrics for plotting from the current infosets.
        
        For Clairvoyance:
        - Bluff frequency: Average probability that a player with a queen bets (action index 1).
        - Calling frequency: Average probability that a player with a king calls (action index 2).
        - Expected values for player 1 and player 2 (zero-sum game).
        
        Parameters:
            infosets (dict): Dictionary mapping info set keys to InformationSet objects.
            expected_game_value (float): Cumulative expected game value.
            iteration (int): Current iteration number.
        
        Returns:
            dict: A dictionary with keys 'iteration', 'bluff_freq', 'call_freq', 'expected_value_p1', 'expected_value_p2'.
        """
        bluff_values = []
        call_values = []
        
        # Iterate over infosets and filter by the card in the key
        for key, infoset in infosets.items():
            # Assume keys starting with 'Q' belong to the player holding the queen (bluff decision)
            if key.startswith('Q'):
                if 1 in infoset.available_actions:  # 1 corresponds to 'Bet'
                    avg_strategy = infoset.get_average_strategy()
                    idx = list(infoset.available_actions).index(1)
                    bluff_values.append(avg_strategy[idx])
            # Assume keys starting with 'K' belong to the player holding the king (calling decision)
            if key.startswith('K'):
                if 2 in infoset.available_actions:  # 2 corresponds to 'Call'
                    avg_strategy = infoset.get_average_strategy()
                    idx = list(infoset.available_actions).index(2)
                    call_values.append(avg_strategy[idx])
        
        bluff_freq = sum(bluff_values) / len(bluff_values) if bluff_values else 0
        call_freq = sum(call_values) / len(call_values) if call_values else 0
        utility = expected_game_value / iteration
        
        return {
            'iteration': iteration,
            'bluff_freq': bluff_freq,
            'call_freq': call_freq,
            'expected_value_p1': utility,
            'expected_value_p2': -utility
        }
        
    def get_plot_config(self):
        """
        Returns the default plot configuration for the Clairvoyance game.
        
        This includes the overall chart title, each subplot's title, series names,
        and (optionally) colors. Colors are optional; if omitted, defaults will be used.
        """
        return {
            "chart_title": f"Equilibrium Strategies and EV in Clairvoyance (Ante={self.ante}, Bet={self.bet_size})",
            "subplots": [
                {
                    "title": "Equilibrium Frequencies",
                    "series": [
                        {"metric": "bluff_freq", "name": "IP Bluffing Frequency", "color": "cyan"},
                        {"metric": "call_freq", "name": "OOP Calling Frequency", "color": "orange"}
                    ]
                },
                {
                    "title": "Expected Value",
                    "series": [
                        {"metric": "expected_value_p1", "name": "IP Expected Value", "color": "red"},
                        {"metric": "expected_value_p2", "name": "OOP Expected Value", "color": "green"}
                    ]
                }
            ]
        }