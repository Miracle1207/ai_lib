# -*- coding:utf-8  -*-

import copy
from gym.utils import seeding
from env.simulators.game import Game
from env.obs_interfaces.observation import *
from utils.discrete import Discrete
from pettingzoo.utils.agent_selector import agent_selector
from rlcard.games.nolimitholdem import Action
import pygame
import os
import random

import numpy as np
import rlcard
from gym import spaces

try:
    from pettingzoo import AECEnv
    from pettingzoo.utils import wrappers
except:
    raise ImportError("The multiplayer Texas hold'em has dependencies on pettingzoo")


from collections import OrderedDict
from rlcard.envs import Env
from env.raw_bridge.game import BridgeGame
from env.raw_bridge.utils.action_event import ActionEvent
from env.raw_bridge.utils.bridge_card import BridgeCard
from env.raw_bridge.utils.move import CallMove, PlayCardMove

def get_image(path):
    from os import path as os_path
    cwd = os_path.dirname(__file__)
    image = pygame.image.load(cwd + '/' + path)
    return image


def get_font(path, size):
    from os import path as os_path
    cwd = os_path.dirname(__file__)
    font = pygame.font.Font((cwd + '/' + path), size)
    return font


class BridgeBase(AECEnv):
    metadata={"render.modes":['human']}

    def __init__(self, name, num_players, obs_shape=None):
        super().__init__()
        self.name=name
        self.num_players = num_players
        config = {"allow_step_back": False, "seed": None}
        self.env = BridgeEnv(config)
        self.screen = None
        self.agents = [f"player_{i}" for i in range(self.env.game.get_num_players())]
        self.possible_agents = self.agents[:]

        dtype = self.env.reset()[0]['obs'].dtype
        if dtype == np.dtype(np.int64):
            self._dtype = np.dtype(np.int8)
        elif dtype == np.dtype(np.float64):
            self._dtype = np.dtype(np.float32)
        else:
            self._dtype = dtype

        obs_shape=[2]*481+[91]*40+[2]*52

        self.observation_spaces = self._convert_to_dict(
            [spaces.Dict({"observation": spaces.MultiDiscrete(obs_shape, dtype=self._dtype),
                          "action_mask": spaces.Box(low=0, high=1, shape=(self.env.num_actions,),
                                                    dtype=np.int8)}) for _ in range(self.num_agents)]
        )

        self.action_spaces = self._convert_to_dict([spaces.Discrete(self.env.num_actions) for _ in range(self.num_agents)])

        self.action_record = {}
        self.last_agent_selection = None

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def seed(self, seed=None):
        config = {'allow_step_back': False,
                  'seed': seed,}
        self.env = BridgeEnv(config)

    def _scale_rewards(self, reward):
        return reward

    def _int_to_name(self, ind):
        return self.possible_agents[ind]

    def _name_to_int(self, name):
        return self.possible_agents.index(name)

    def _convert_to_dict(self, list_of_list):
        return dict(zip(self.possible_agents, list_of_list))

    def observe(self, agent):
        obs = self.env.get_state(self._name_to_int(agent))
        observation = obs['obs'].astype(self._dtype)

        legal_moves = self.next_legal_moves
        action_mask = np.zeros(self.env.num_actions, 'int8')
        for i in legal_moves:
            action_mask[i] = 1

        return {'observation': observation, 'action_mask': action_mask}

    def step(self, action):
        if self.dones[self.agent_selection]:
            return self._was_done_step(action)

        self.action_record[self.agent_selection] = action
        self.last_agent_selection = self.agent_selection

        obs, next_player_id = self.env.step(action)
        next_player = self._int_to_name(next_player_id)
        self._last_obs = self.observe(self.agent_selection)
        if self.env.is_over():
            self.rewards = self._convert_to_dict(self._scale_rewards(self.env.get_payoffs()))
            self.next_legal_moves = []
            self.dones = self._convert_to_dict([True if self.env.is_over() else False for _ in range(self.num_agents)])
        else:
            self.next_legal_moves = list(sorted(obs['legal_actions']))
        self._cumulative_rewards[self.agent_selection] = 0
        self.agent_selection = next_player
        self._accumulate_rewards()
        self._dones_step_first()

    def reset(self):
        obs, player_id = self.env.reset()

        self.agents = self.possible_agents[:]
        self.agent_selection = self._int_to_name(player_id)
        self.rewards = self._convert_to_dict([0 for _ in range(self.num_agents)])
        self._cumulative_rewards = self._convert_to_dict([0 for _ in range(self.num_agents)])
        self.dones = self._convert_to_dict([False for _ in range(self.num_agents)])
        self.infos = self._convert_to_dict([{'legal_moves': []} for _ in range(self.num_agents)])
        self.next_legal_moves = list(sorted(obs['legal_actions']))
        self._last_obs = obs['obs']


class BridgeRender(BridgeBase):
    metadata = {'render.modes': ['human', 'rgb_array'], "name": "bridge"}

    def __init__(self, num_players=4):
        super().__init__('bridge', num_players)

    def render(self, mode='human'):
        screen_height = 2000
        screen_width = 2000

        if self.screen is None:
            if mode == "human":
                pygame.init()
                self.screen = pygame.display.set_mode((screen_width, screen_height))
            else:
                pygame.font.init()
                self.screen = pygame.Surface((screen_width, screen_height))

        if mode == "human":
            pygame.event.get()

        def calculate_width(self, screen_width, i):
            return int((screen_width / (np.ceil(len(self.possible_agents) / 2) + 1) * np.ceil((i + 1) / 2)) + (tile_size * 31 / 616))

        def calculate_offset(hand, j, tile_size):
            return int((len(hand) * (tile_size * 23 / 56)) - ((j) * (tile_size * 23 / 28)))

        def calculate_height(screen_height, divisor, multiplier, tile_size, offset):
            return int(multiplier * screen_height / divisor + tile_size * offset)

        tile_size = screen_height  /7
        tile_short_edge = tile_size*(142/197)

        bg_color = (7, 99, 36)
        white = (255, 255, 255)
        cyan = (0,255,255)
        red = (255,0,0)
        horizontal_card_gap = 60
        vertical_card_gap = 80
        self.screen.fill(bg_color)
        pid = ["N", "E", "S", "W"]

        for i, player in enumerate(self.possible_agents):
            players_hand = self.env.game.round.players[i].hand
            for j, card in enumerate(players_hand):
                card_img = get_image(os.path.join(f"Texas_Holdem/img/{str(card)[::-1]}.png"))
                card_img = pygame.transform.scale(card_img, (int(tile_short_edge), int(tile_size)))

                if i%2 == 0:
                    self.screen.blit(card_img,
                                     (screen_width/2-int(tile_short_edge)/2-len(players_hand)/2*horizontal_card_gap
                                      +horizontal_card_gap*j,
                                      screen_height/6*(i*2+1)-tile_size/2))
                else:
                    self.screen.blit(card_img,
                                     (screen_width-screen_width/6*(2*i-1)-tile_short_edge/2,
                                     screen_height/2-int(tile_size)/2-len(players_hand)/2*vertical_card_gap
                                      +vertical_card_gap*j))

            font = get_font(os.path.join(f'Texas_Holdem/font/Minecraft.ttf'), 36)
            _text = f"Player {str(i)} - {pid[i]}"
            text = font.render(_text, True, white)
            textRect = text.get_rect()
            if i%2==0:
                textcenter = (screen_width/2, screen_height/6*(i*2+1)+(i-1)*tile_size/2+40*(i-1))
            else:
                textcenter = (screen_width-screen_width/6*(2*i-1)-(i-2)*tile_short_edge/2-100*(i-2), screen_height/2)
            textRect.center = textcenter

            self.screen.blit(text, textRect)



        if mode == "human":
            pygame.display.update()

        if mode == "rgb_array":
            observation = np.array(pygame.surfarray.pixels3d(self.screen))
        else:
            observation = None
        return observation





class BridgeEnv(Env):
    ''' Bridge Environment from rlcard
    '''

    def __init__(self, config):
        self.name = 'bridge'
        self.game = BridgeGame()
        super().__init__(config=config)
        self.bridgePayoffDelegate = DefaultBridgePayoffDelegate()
        self.bridgeStateExtractor = DefaultBridgeStateExtractor()
        state_shape_size = self.bridgeStateExtractor.get_state_shape_size()
        self.state_shape = [[1, state_shape_size] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]


    def get_payoffs(self):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''
        return self.bridgePayoffDelegate.get_payoffs(game=self.game)

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        return self.game.round.get_perfect_information()

    def _extract_state(self, state):  # wch: don't use state 211126
        ''' Extract useful information from state for RL.

        Args:
            state (dict): The raw state

        Returns:
            (numpy.array): The extracted state
        '''
        return self.bridgeStateExtractor.extract_state(game=self.game)

    def _decode_action(self, action_id):
        ''' Decode Action id to the action in the game.

        Args:
            action_id (int): The id of the action

        Returns:
            (ActionEvent): The action that will be passed to the game engine.
        '''
        return ActionEvent.from_action_id(action_id=action_id)

    def _get_legal_actions(self):
        ''' Get all legal actions for current state.

        Returns:
            (list): A list of legal actions' id.
        '''
        raise NotImplementedError  # wch: not needed


class BridgePayoffDelegate(object):

    def get_payoffs(self, game: BridgeGame):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            (list): A list of payoffs for each player.

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError


class DefaultBridgePayoffDelegate(BridgePayoffDelegate):

    def __init__(self):
        self.make_bid_bonus = 2

    def get_payoffs(self, game: BridgeGame):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''
        contract_bid_move = game.round.contract_bid_move
        if contract_bid_move:
            declarer = contract_bid_move.player
            bid_trick_count = contract_bid_move.action.bid_amount + 6
            won_trick_counts = game.round.won_trick_counts
            declarer_won_trick_count = won_trick_counts[declarer.player_id % 2]
            defender_won_trick_count = won_trick_counts[(declarer.player_id + 1) % 2]
            declarer_payoff = bid_trick_count + self.make_bid_bonus if bid_trick_count <= declarer_won_trick_count else declarer_won_trick_count - bid_trick_count
            defender_payoff = defender_won_trick_count
            payoffs = []
            for player_id in range(4):
                payoff = declarer_payoff if player_id % 2 == declarer.player_id % 2 else defender_payoff
                payoffs.append(payoff)
        else:
            payoffs = [0, 0, 0, 0]
        return np.array(payoffs)


class BridgeStateExtractor(object):  # interface

    def get_state_shape_size(self) -> int:
        raise NotImplementedError

    def extract_state(self, game: BridgeGame):
        ''' Extract useful information from state for RL. Must be implemented in the child class.

        Args:
            game (BridgeGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        raise NotImplementedError

    @staticmethod
    def get_legal_actions(game: BridgeGame):
        ''' Get all legal actions for current state.

        Returns:
            (OrderedDict): A OrderedDict of legal actions' id.
        '''
        legal_actions = game.judger.get_legal_actions()
        legal_actions_ids = {action_event.action_id: None for action_event in legal_actions}
        return OrderedDict(legal_actions_ids)


class DefaultBridgeStateExtractor(BridgeStateExtractor):

    def __init__(self):
        super().__init__()
        self.max_bidding_rep_index = 40  # Note: max of 40 calls
        self.last_bid_rep_size = 1 + 35 + 3  # no_bid, bid, pass, dbl, rdbl

    def get_state_shape_size(self) -> int:
        state_shape_size = 0
        state_shape_size += 4 * 52  # hands_rep_size
        state_shape_size += 4 * 52  # trick_rep_size
        state_shape_size += 52  # hidden_cards_rep_size
        state_shape_size += 4  # vul_rep_size
        state_shape_size += 4  # dealer_rep_size
        state_shape_size += 4  # current_player_rep_size
        state_shape_size += 1  # is_bidding_rep_size
        state_shape_size += self.max_bidding_rep_index  # bidding_rep_size
        state_shape_size += self.last_bid_rep_size  # last_bid_rep_size
        state_shape_size += 8  # bid_amount_rep_size
        state_shape_size += 5  # trump_suit_rep_size
        return state_shape_size

    def extract_state(self, game: BridgeGame):
        ''' Extract useful information from state for RL.

        Args:
            game (BridgeGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        extracted_state = {}
        legal_actions: OrderedDict = self.get_legal_actions(game=game)
        raw_legal_actions = list(legal_actions.keys())
        current_player = game.round.get_current_player()
        current_player_id = current_player.player_id

        # construct hands_rep of hands of players
        hands_rep = [np.zeros(52, dtype=int) for _ in range(4)]
        if not game.is_over():
            for card in game.round.players[current_player_id].hand:
                hands_rep[current_player_id][card.card_id] = 1
            if game.round.is_bidding_over():
                dummy = game.round.get_dummy()
                other_known_player = dummy if dummy.player_id != current_player_id else game.round.get_declarer()
                for card in other_known_player.hand:
                    hands_rep[other_known_player.player_id][card.card_id] = 1

        # construct trick_pile_rep
        trick_pile_rep = [np.zeros(52, dtype=int) for _ in range(4)]
        if game.round.is_bidding_over() and not game.is_over():
            trick_moves = game.round.get_trick_moves()
            for move in trick_moves:
                player = move.player
                card = move.card
                trick_pile_rep[player.player_id][card.card_id] = 1

        # construct hidden_card_rep (during trick taking phase)
        hidden_cards_rep = np.zeros(52, dtype=int)
        if not game.is_over():
            if game.round.is_bidding_over():
                declarer = game.round.get_declarer()
                if current_player_id % 2 == declarer.player_id % 2:
                    hidden_player_ids = [(current_player_id + 1) % 2, (current_player_id + 3) % 2]
                else:
                    hidden_player_ids = [declarer.player_id, (current_player_id + 2) % 2]
                for hidden_player_id in hidden_player_ids:
                    for card in game.round.players[hidden_player_id].hand:
                        hidden_cards_rep[card.card_id] = 1
            else:
                for player in game.round.players:
                    if player.player_id != current_player_id:
                        for card in player.hand:
                            hidden_cards_rep[card.card_id] = 1

        # construct vul_rep
        vul_rep = np.array(game.round.tray.vul, dtype=int)

        # construct dealer_rep
        dealer_rep = np.zeros(4, dtype=int)
        dealer_rep[game.round.tray.dealer_id] = 1

        # construct current_player_rep
        current_player_rep = np.zeros(4, dtype=int)
        current_player_rep[current_player_id] = 1

        # construct is_bidding_rep
        is_bidding_rep = np.array([1] if game.round.is_bidding_over() else [0])

        # construct bidding_rep
        bidding_rep = np.zeros(self.max_bidding_rep_index, dtype=int)
        bidding_rep_index = game.round.dealer_id  # no_bid_action_ids allocated at start so that north always 'starts' the bidding
        for move in game.round.move_sheet:
            if bidding_rep_index >= self.max_bidding_rep_index:
                break
            elif isinstance(move, PlayCardMove):
                break
            elif isinstance(move, CallMove):
                bidding_rep[bidding_rep_index] = move.action.action_id
                bidding_rep_index += 1

        # last_bid_rep
        last_bid_rep = np.zeros(self.last_bid_rep_size, dtype=int)
        last_move = game.round.move_sheet[-1]
        if isinstance(last_move, CallMove):
            last_bid_rep[last_move.action.action_id - ActionEvent.no_bid_action_id] = 1

        # bid_amount_rep and trump_suit_rep
        bid_amount_rep = np.zeros(8, dtype=int)
        trump_suit_rep = np.zeros(5, dtype=int)
        if game.round.is_bidding_over() and not game.is_over() and game.round.play_card_count == 0:
            contract_bid_move = game.round.contract_bid_move
            if contract_bid_move:
                bid_amount_rep[contract_bid_move.action.bid_amount] = 1
                bid_suit = contract_bid_move.action.bid_suit
                bid_suit_index = 4 if not bid_suit else BridgeCard.suits.index(bid_suit)
                trump_suit_rep[bid_suit_index] = 1

        rep = []
        rep += hands_rep
        rep += trick_pile_rep
        rep.append(hidden_cards_rep)
        rep.append(vul_rep)
        rep.append(dealer_rep)
        rep.append(current_player_rep)
        rep.append(is_bidding_rep)
        rep.append(bidding_rep)
        rep.append(last_bid_rep)
        rep.append(bid_amount_rep)
        rep.append(trump_suit_rep)

        obs = np.concatenate(rep)
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = legal_actions
        extracted_state['raw_legal_actions'] = raw_legal_actions
        extracted_state['raw_obs'] = obs
        return extracted_state



if __name__ == '__main__':
    cfg = {'seed': 42, "allow_step_back": False}
    raw_env = BridgeEnv(cfg)

    # pettingzoo_env = BridgeBase(name='bridge', num_players=4)
    # pettingzoo_env.reset()
    env = BridgeRender()
    env.reset()
    done = env.dones
    while not any(done.values()):
        action = np.random.choice(env.next_legal_moves)
        env.step(action)
        done = env.dones
        env.render()
    print(1)




