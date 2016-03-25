#!/usr/bin/env python

import sys
import math

from gsp import GSP
from util import argmax_index

class Fwrkbudget:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget

    def initial_bid(self, reserve):
        return 0 #self.value / 2


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

        def util(i):
            pos_effect = math.pow(0.75, i)
            init_util = value - slot_info_copy[i][1]
            return pos_effect * init_util

        utilities = [util(i) for i in range(len(slot_info_copy))]

        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """
        i =  argmax_index(self.expected_utils(t, history, reserve))
        info = self.slot_info(t, history, reserve)

        return info[i]

    def bid(self, t, history, reserve):

        # print "Occupants of round %d are: " % (t - 1)
        # print history.round(t-1).occupants

        # balanced bidder with periodic weight

        periodic_weight = (30 + math.cos(math.pi * t / 24) + 50) / 80
        budget_cap = self.budget / 48

        prev_round = history.round(t-1)
        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        bid = 0
        if min_bid >= self.value or slot == 0:
            bid = self.value
        else:
            # bid = self.value - (math.pow(0.75, slot) * (self.value - max_bid) / math.pow(0.75, slot - 1))
            bid = self.value - 0.75 * (self.value - min_bid)

        periodic_weight = (math.cos(math.pi * t / 24))
        bid = bid

        # print history.round(t-1).bids
        # print "bid %f for slot %d in round %d" % (bid, slot, t)

        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)
