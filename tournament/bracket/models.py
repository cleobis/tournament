from django.db import models
import math

# Create your models here.

# class MatchPerson(model.Model):
#     name
#     match
#     prev_match
#     points
#     disqualified

class Match():
    # prev_matches
    # winner_match
    # consolation_match
    # aka
    # shiro
    # done
    # winner
    
    def __init__(self):
        self.winner_match = None
        self.consolation_match = None
        self.num_round = 0
        self.str = ""


class Bracket1Elim():
    
    # people
    # matches
    
    
    def __init__(self):
        self.final_match = None
        self.consolation_match = None
    
    
    def build_test(self, round=0, match=0, parent=None):
        
        if round == 0:
            self.final_match = Match()
            m = self.final_match
            m.str = "final"
            m.prev_matches = [
                self.build_test(round+1, 0, m),
                self.build_test(round+1, 1, m),
            ]
            
            self.consolation_match = Match()
            for m in self.final_match.prev_matches:
                m.consolation_match = self.consolation_match
            
            self.num_round = 3
            
        elif round == 1:
            m = Match()
            m.str = "1"
            m.winner_match = parent
            m.prev_matches = [
                self.build_test(round+1, 0 + 2 * match, m),
            ]
            # if match == 1:
            #     m.prev_matches.append(
            #         self.build_test(round+1, 1 + 2 * match, m))
            
            return m
        
        elif round == 2:
            m = Match()
            m.str = "2"
            m.winner_match = parent
            m.prev_matches = []
            return m
            
        else:
            raise ArgumentError("Unexpected round {}.".format(round))
    
    
    def get_num_round(self):
        # return math.ceil(math.log2(len(self.people)))
        return int(self.num_round)
    
    
    def get_num_match_in_round(self, round=None):
        if round is None:
            # Can't pass argument from template. Return array.
            return [ math.pow(2, round) for round in range(0,self.get_num_round()) ]
        else:
            return math.pow(2, round)
    
    
    def get_match(self, round, match_i):
        #       2    1      0
        # 0 ----\____
        # 1 ----/    \____
        # 2      ____/    \
        # 3                \____
        # 4 ----\____      /
        # 5 ----/    \____/
        # 6      ____/
        # 7                 ____
        
        if round // 1 != round or round < 0 or self.get_num_round() <= round:
            raise ValueError("Invalid round {}.".format(round))
        split = -1
        m = self.final_match
        for i_round in range(round):
            split = self.get_num_match_in_round(round - i_round - 1)
            if match_i < split:
                m = m.prev_matches[0] if len(m.prev_matches) >= 1 else None
            elif match_i < 2 * split:
                match_i -= split
                m = m.prev_matches[1] if len(m.prev_matches) >= 2 else None
            else:
                m = None
            
            if m is None:
                break
                
        # return {'round': round, 'split': split, 'str': m.str if m is not None else "",
            # 'kids': m.prev_matches if m is not None else []}
        return m


