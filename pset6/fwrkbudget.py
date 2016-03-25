#!/usr/bin/env python

import sys
import math

from gsp import GSP
from util import argmax_index

class Fwrkbudget:
    """Budget-aware agent"""

    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget

    def initial_bid(self, reserve):
        bid = self.value / 3
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

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """

        # print self.expected_utils(t, history, reserve)
        # i =  argmax_index(self.expected_utils(t, history, reserve))
        # i = len(self.expected_utils(t, history, reserve)) - 1
        i = len(history.round(t - 1).clicks) - 1
        info = self.slot_info(t, history, reserve)

        return info[i]

    def bid(self, t, history, reserve):
        # Applies balanced bidding strategy, but
        # always goes for the last slot

        target_slot = self.target_slot(t, history, reserve)

        bid = 0
        (slot, min_bid, max_bid) = target_slot
        if min_bid >= self.value or slot <= 0:
            bid = self.value
        else:
            bid = self.value - 0.75 * (self.value - min_bid)

        cos_cycle = (math.cos(math.pi * t / 24))
        bid = bid - cos_cycle

        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)
