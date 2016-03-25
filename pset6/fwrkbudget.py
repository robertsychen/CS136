#!/usr/bin/env python

import sys
import math

from gsp import GSP
from util import argmax_index

class Fwrkbudget:
    """Budget-aware agent"""

    epsilon = 0.1

    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.total_spent = 0

    def initial_bid(self, reserve):
        bid = self.value / 2
        self.total_spent += bid
        return bid


    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)

        clicks = prev_round.clicks
        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max == None:
                max = 2 * min
            return (s, min, max)
        info = map(compute, range(len(clicks)))
        # sys.stdout.write("slot info: %s\n" % info)

        return info


    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        returns a list of utilities per slot.
        """
        slot_info_copy = self.slot_info(t, history, reserve)
        value = self.value

        def util((slot, min_bid, max_bid)):
            pos_effect = math.pow(0.75, slot)
            init_util = value - min_bid
            utility = pos_effect * init_util
            return (slot, utility, min_bid)

        utilities = map(util, slot_info_copy)

        return utilities

    def bid_threshold(self):
        U = self.value + 1
        z = self.total_spent / self.budget
        phi = math.pow((U * math.e / self.epsilon), z) * (self.epsilon / math.e)
        return self.value / (1 + phi)

    def target_slot(self, t, history, reserve, threshold):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """

        # slots = self.expected_utils(t, history, reserve)
        # slots = filter(lambda (slot, utility, min_bid): min_bid <= threshold, slots)
        #
        # if slots:
        #     i = max(slots, key=lambda (a, b, c): b)[0]
        # else:
        #     i = None
        #
        # info = self.slot_info(t, history, reserve)
        #
        # return info[i] if i is not None else None

        i =  argmax_index(self.expected_utils(t, history, reserve))
        info = self.slot_info(t, history, reserve)

        return info[i]

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # - targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - t_s(j))}.
        # - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - t_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # (p_x is the price/click in slot x)
        # If s*_j is the top slot, bid the value v_j

        prev_round = history.round(t-1)
        threshold = self.bid_threshold()
        target_slot = self.target_slot(t, history, reserve, threshold)

        bid = 0
        if target_slot is None:
            bid = 1
        else:
            (slot, min_bid, max_bid) = target_slot
            if slot == 0:
                bid = self.value
            else:
                bid = min_bid

        self.total_spent += bid

        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)
