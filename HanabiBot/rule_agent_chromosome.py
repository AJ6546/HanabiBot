# A rule-based hanabi agent driven by a chromosome.
# The objective of this class is to be a starter-class for a larger set of rules.
# M. Fairbank. November 2021.
from hanabi_learning_environment.rl_env import Agent
import random
def argmax(llist):
    #useful function for arg-max
    return llist.index(max(llist))
    
class RuleAgentChromosome(Agent):
    """Agent that applies a simple heuristic."""

    def __init__(self, config, chromosome=[1, 11, 2, 7, 5, 8, 6], *args, **kwargs):# TODO replace this default chromosome with something better, if possible.  Plus, Add new bespoke rules below if necessary.
        """Initialize the agent."""
        self.config = config
        self.chromosome=chromosome
        self.turn=0
        self.played_cards = []
        self.unplayable_cards = []
        assert isinstance(chromosome, list)
        
        # Extract max info tokens or set default to 8.
        self.max_information_tokens = config.get('information_tokens', 8)

    def calculate_all_unseen_cards(self, discard_pile, player_hands, fireworks):
        # All of the cards which we can't see are either in our own hand or in the deck.
        # The other cards must be in the discard pile (all cards of which we have seen and remembered) or in other player's hands.
        colors = ['Y', 'B', 'W', 'R', 'G']
        full_hanabi_deck=[{"color":c, "rank":r} for c in colors for r in [0,0,0,1,1,2,2,3,3,4]]
        assert len(full_hanabi_deck)==50 # full hanabi deck size.

        result=full_hanabi_deck
        # subract off all cards that have been discarded...
        for card in discard_pile:
            if card in result:
                result.remove(card)
        
        # subract off all cards that we can see in the other players' hands...
        for hand in player_hands[1:]:
            for card in hand:
                if card in result:
                    result.remove(card)

        for (color, height) in fireworks.items():
            for rank in range(height):
                card={"color":color, "rank":rank}
                if card in result:
                    result.remove(card)

        # Now we left with only the cards we have never seen before in the game (so these are the cards in the deck UNION our own hand).
        return result             
    def filter_played_cards(self, fireworks):
        for (color, height) in fireworks.items():
            for rank in range(height):
                card={"color":color, "rank":rank}
                if card not in self.played_cards:
                    self.played_cards.append(card)
        return self.played_cards    

    def filter_card_list_by_hint(self, card_list, hint):
        # This could be enhanced by using negative hint information, available from observation['pyhanabi'].card_knowledge()[player_offset][card_number]
        filtered_card_list=card_list
        if hint["color"]!=None:
            filtered_card_list=[c for c in filtered_card_list if c["color"]==hint["color"]]
        if hint["rank"]!=None:
            filtered_card_list=[c for c in filtered_card_list if c["rank"]==hint["rank"]]
        return filtered_card_list


    def filter_card_list_by_playability(self, card_list, fireworks):
        # find out which cards in card list would fit exactly onto next value of its colour's firework
        return [c for c in card_list if self.is_card_playable(c,fireworks)]

    def filter_card_list_by_unplayable(self, card_list, fireworks, discard_pile):
        # find out which cards in card list are always going to be unplayable on its colour's firework
        # This function could be improved by considering that we know a card of value 5 will never be playable if all the 4s for that colour have been discarded.
        colors = ['Y', 'B', 'W', 'R', 'G']
        #self.unplayable_cards.clear()
        for c in colors:
            count=[0,0,0,0]
            for card in discard_pile:
                if c == card['color'] and card not in self.unplayable_cards:
                    r = card['rank']
                    if r == 0:
                        count[0]+=1
                    elif r == 1:
                        count[1]+=1
                    elif r == 2:                              
                        count[2]+=1
                    elif r == 3:                              
                        count[3]+=1
                    if count[0]==3 or count[1] == 2 or count[2] == 2 or count[3] == 2:
                        for cd in card_list:
                            if cd['color'] == c and cd['rank'] > r and cd not in self.unplayable_cards:
                                self.unplayable_cards.append(cd)
        for c in card_list:
            if c["rank"]<=fireworks[c["color"]] and c not in self.unplayable_cards:
                self.unplayable_cards.append(c)
        return [c for c in self.unplayable_cards ]

    #Color that cannot be played
    def filter_unplayable_Color(self, discard_pile, fireworks):
        colors = ['Y', 'B', 'W', 'R', 'G']
        full_hanabi_deck=[{"color":c, "rank":r} for c in colors for r in [0,0,0,1,1,2,2,3,3,4]]
        result=full_hanabi_deck
        playable_colors={'Y':False,'B':False, 'W':False, 'R':False,'G':False}
        # subract off all cards that have been discarded...
        for card in discard_pile:
            if card in result:
                result.remove(card)  
        # subtract cards already in the firework
        for (color, height) in fireworks.items():
            for rank in range(height):
                card={"color":color, "rank":rank}
                if card in result:
                    result.remove(card)
        for card in result:
            if card['rank'] >= fireworks[card['color']]:
                playable_colors[card['color']]=True
        unplayable_colors=[]
        for c in playable_colors.keys():
            if playable_colors[c]==False:
                unplayable_colors.append(c)
        return unplayable_colors
        


    def is_card_playable(self, card, fireworks):
        return card['rank'] == fireworks[card['color']]

    def act(self, observation):
        # this function is called for every player on every turn
        """Act based on an observation."""
        if observation['current_player_offset'] != 0:
            # but only the player with offset 0 is allowed to make an action.  The other players are just observing.
            return None
         # Remove duplicates of already played cards
        fireworks = observation['fireworks']
        card_hints=observation['card_knowledge'][0] # This [0] produces the card hints for OUR own hand (player offset 0)
        hand_size=len(card_hints)
        
        # build some useful lists of information about what we hold in our hand and what team-mates know about their hands.
        all_unseen_cards=self.calculate_all_unseen_cards(observation['discard_pile'],observation['observed_hands'],observation['fireworks'])
        possible_cards_by_hand=[self.filter_card_list_by_hint(all_unseen_cards, h) for h in card_hints]
        playable_cards_by_hand=[self.filter_card_list_by_playability(posscards, fireworks) for posscards in possible_cards_by_hand]
        probability_cards_playable=[len(playable_cards_by_hand[index])/len(possible_cards_by_hand[index]) for index in range(hand_size)]
        played_cards=self.filter_played_cards(observation['fireworks'])
        useless_cards_by_hand=[self.filter_card_list_by_unplayable(posscards, fireworks, observation['discard_pile']) for posscards in possible_cards_by_hand]
        probability_cards_useless=[len(useless_cards_by_hand[index])/len(possible_cards_by_hand[index]) for index in range(hand_size)]
        unplayable_colors= self.filter_unplayable_Color(observation['discard_pile'], observation['fireworks'])
        #print(unplayable_colors)   
        # based on the above calculations, try a sequence of rules in turn and perform the first one that is applicable:
        for rule in self.chromosome:
            if rule in [0,1]:
                # Play any highly-probable playable cards:
                threshold=0.8 if rule==0 else 0.5
                if max(probability_cards_playable)>threshold:
                    return {'action_type': 'PLAY', 'card_index': argmax(probability_cards_playable)}

            elif rule==2:
                # Check if it's possible to hint a card to your colleagues.  TODO this could be split into 2 separate rules?
                if observation['information_tokens'] > 0:
                    # Check if there are any playable cards in the hands of the opponents.
                    for player_offset in range(1, observation['num_players']):
                        player_hand = observation['observed_hands'][player_offset]
                        player_hints = observation['card_knowledge'][player_offset]
                        # Check if the card in the hand of the opponent is playable.
                        for card, hint in zip(player_hand, player_hints):
                            if self.is_card_playable(card,fireworks):
                                if hint['color'] is None:
                                    return {
                                        'action_type': 'REVEAL_COLOR',
                                        'color': card['color'],
                                        'target_offset': player_offset
                                    }
                                elif hint['rank'] is None:
                                    return {
                                        'action_type': 'REVEAL_RANK',
                                        'rank': card['rank'],
                                        'target_offset': player_offset
                                    }
            elif rule in [3,4]:
                # discard any highly-probable useless cards:
                threshold=0.8 if rule==3 else 0.5
                if observation['information_tokens'] < self.max_information_tokens:
                    if max(probability_cards_useless)>threshold:
                        card_index=argmax(probability_cards_useless)
                        return {'action_type': 'DISCARD', 'card_index': card_index}

            elif rule==5:
                # Discard something
                if observation['information_tokens'] < self.max_information_tokens:

                    return {'action_type': 'DISCARD', 'card_index': 0}# discards the oldest card (card_index 0 will be oldest card)
            elif rule==6:
                # Play our best-hope card
                return {'action_type': 'PLAY', 'card_index': argmax(probability_cards_playable)}
        
            elif rule==7:
                #Play card with both rank and color
                if observation['life_tokens'] == 1:
                    player_hand = observation['observed_hands'][0]
                    player_hints = observation['card_knowledge'][0]
                    for hint in player_hints:
                        if hint['color'] is not None and hint['rank'] is not None and self.is_card_playable(hint,fireworks):
                            return {'action_type': 'PLAY', 'card_index': player_hints.index(hint)}
            elif rule==8:
                #Play a card with rank required on the firework
                if observation['information_tokens'] == 0 and observation['life_tokens']>=3:
                    player_hints = observation['card_knowledge'][0]
                    for hint in player_hints:
                        if hint['rank'] is not None and hint['rank'] in fireworks.values():
                            return {'action_type': 'PLAY', 'card_index': player_hints.index(hint)}
            elif rule==9:
                #Discard an unplayable card
                if observation['information_tokens'] == 0:
                    player_hints = observation['card_knowledge'][0]
                    for hint in player_hints:
                        for card in self.unplayable_cards:
                            if hint['rank'] is not None and hint['rank']==card['rank'] and hint['color']==card['color']:
                                return {'action_type': 'DISCARD', 'card_index': player_hints.index(hint)}
            elif rule==10:
                # If you have hint on an unplayable color, discard that card
                if observation['information_tokens'] < 3:
                    player_hints = observation['card_knowledge'][0]
                    for hint in player_hints:
                        for color in unplayable_colors:
                            if hint['color'] is not None and hint['color']==color:
                                return {'action_type': 'DISCARD', 'card_index': player_hints.index(hint)}
            elif rule==11:
                # Give a player with no clues a clue about playable card
                if observation['information_tokens'] > 0:
                    # Check if there are any playable cards in the hands of the opponents.
                    player_index=None
                    hints=0
                    for player_offset in range(1, observation['num_players']):
                        player_hints = observation['card_knowledge'][player_offset]
                        for hint in player_hints:
                            if hint['color'] is not None or hint['rank'] is not None:
                                hints+=1
                        if hints==0:
                            player_index=player_offset
                    if player_index is not None:
                        player_hand = observation['observed_hands'][player_index]
                        player_hints = observation['card_knowledge'][player_index]
                        # Check if the card in the hand of the opponent is playable.
                        for card, hint in zip(player_hand, player_hints):
                            if self.is_card_playable(card,fireworks):
                                if random.randint(1,2)==1:
                                    return {
                                        'action_type': 'REVEAL_COLOR',
                                        'color': card['color'],
                                        'target_offset': player_index
                                        }
                                elif hint['rank'] is None:
                                    return {
                                        'action_type': 'REVEAL_RANK',
                                        'rank': card['rank'],
                                        'target_offset': player_index
                                        }

            else:
                # the chromosome contains an unknown rule
                raise Exception("Rule not defined: "+str(rule))
        # The chromosome needs to be defined so the program never gets to here.  
        # E.g. always include rules 5 and 6 in the chromosome somewhere to ensure this never happens..        
        raise Exception("No rule fired for game situation - faulty rule set",  self.chromosome)
