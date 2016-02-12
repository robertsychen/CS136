#!/usr/bin/python

# This is the reference client. It's based on the BitTorrent protocol.

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer
from collections import Counter
import itertools

class FwrkStd(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "rainbows and sparkles :)"
        # reciprocal unlocking
        # for easy tracking of one/two round download histories
        self.one_round_ago = dict()
        self.two_round_ago = dict()
        # optimistic unlocking
        # we'll update this automatically in round 0,
        # so let's set it to -1 for now
        self.optimistic = -1

    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = filter(needed, range(len(self.pieces)))
        np_set = set(needed_pieces)  # sets support fast intersection ops.

        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        # combine all pieces, and flatten the list

        # a simple assumption: when we say 'rarest pieces'
        # we mean only those among everyone else!
        # (this is a fine assumption, so we won't request
        # own pieces anyway)
        all_available_pieces = list(itertools.chain(*[p.available_pieces for p in peers]))
        # now order by frequency
        pieces_by_frequency = Counter(all_available_pieces).most_common()

        logging.debug("Here are the most frequent pieces: " + str(pieces_by_frequency))

        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)

        # Sort peers by id.  This is probably not a useful sort, but other
        # sorts might be useful
        peers.sort(key=lambda p: p.id)
        # request all available pieces from all peers!
        # (up to self.max_requests from each)
        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = av_set.intersection(np_set)
            n = min(self.max_requests, len(isect))
            # **Implement rarest pieces first**
            # A simple assumption we can make is to ask for as many
            # as possible from each peer, as in the dummy, but
            # ordering by rarest-first instead of randomly
            num_requested = 0
            curr_rare_piece = 1
            while num_requested < n and curr_rare_piece <= len(pieces_by_frequency):
                rare_id = pieces_by_frequency[-1*curr_rare_piece][0]
                if rare_id in isect:
                    num_requested += 1
                    # aha! The peer has this piece! Request it.
                    # which part of the piece do we need next?
                    # (must get the next-needed blocks in order)
                    start_block = self.pieces[rare_id]
                    r = Request(self.id, peer.id, rare_id, start_block)
                    requests.append(r)
                curr_rare_piece += 1

        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """

        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        # take care of updating the trackers for your friendliest peers
        self.two_round_ago = self.one_round_ago.copy()
        self.one_round_ago = dict()
        if round != 0:
            for d in history.downloads[round-1]:
                # let's assume that we can just add blocks split among pieces
                # rather than average among pieces
                if d.from_id in self.one_round_ago.keys():
                    self.one_round_ago[d.from_id] += d.blocks
                else:
                    self.one_round_ago[d.from_id] = d.blocks

        logging.debug("Here are my peer histories from two round ago: %s" % self.two_round_ago)
        logging.debug("and from one round ago: %s" % self.one_round_ago)

        # and now add up the last two rounds
        c = Counter(self.two_round_ago)
        c.update(self.one_round_ago)
        best_friends = c.most_common()

        logging.debug("and my best friends!: %s" % best_friends)

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            logging.debug("Still here: uploading to my favorite peers")
            # change my internal state for no reason
            # No! Bad! Keep the cake!
            # self.dummy_state["cake"] = "pie"

            # **Reciprocal unlocking**
            # let's assume that we only want to give to our
            # mostest bestest friends, even if they don't request from us
            # It promotes charity :)

            # Let's also do some handling to randomize if we have multiple best friends
            # of same bestiness
            # most of this is just ugly handling of cases where we don't have enough friends
            chosen = []
            # handle bestest friends either being clear best or also tied
            if len(best_friends) > 2:
                candidate_best_friends = [best_friends[2]]
                best_friend_counter = 3
                # handle best friends tied for bestinees
                while(best_friend_counter < len(best_friends) and best_friends[best_friend_counter][1] == best_friends[2][1]):
                    candidate_best_friends.append(best_friends[best_friend_counter][0])
                    best_friend_counter += 1
                if best_friends[0][1] > best_friends[2][1]:
                    chosen.append(best_friends[0][0])
                else:
                    candidate_best_friends.append(best_friends[0][0])
                if best_friends[1][1] > best_friends[2][1]:
                    chosen.append(best_friends[1][0])
                else:
                    candidate_best_friends.append(best_friends[1][0])
            else:
                candidate_best_friends = []
                if len(best_friends) > 1:
                    chosen.append(best_friends[1][0])
                if len(best_friends) > 0:
                    chosen.append(best_friends[0][0])
            # finally, we can actually randomize
            random.shuffle(candidate_best_friends)
            for i in xrange(3 - len(chosen)):
                # let's assume we're okay leaving best friend slots empty
                if i < len(candidate_best_friends):
                    chosen.append(candidate_best_friends[i])

            # **Optimistic unlocking**
            # Again, let's assume that our optimistic doesn't necessarily
            # have to be in the requests
            # Let's also assume that we won't give to the optimistic
            # if they're already in our best friends--we can wait until they're not,
            # or a new optimistic is set
            if round % 3 == 0:
                self.optimistic = random.choice(peers).id
            if self.optimistic not in chosen:
                chosen.append(self.optimistic)

            logging.debug("And here are my chosen peers: %s", chosen)
            # request = random.choice(requests)
            # chosen = [request.requester_id]
            # Evenly "split" my upload bandwidth among the chosen requesters
            bws = even_split(self.up_bw, len(chosen))

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(chosen, bws)]

        return uploads
