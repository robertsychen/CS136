#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer
from collections import Counter
import itertools

class FwrkPropShare(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"

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

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            # logging.debug("Still here: uploading to a random peer")
            # change my internal state for no reason
            # NO! Keep the cake!!! >:(
            # self.dummy_state["cake"] = "pie"

            one_round_ago = dict()
            if round != 0:
                for d in history.downloads[round-1]:
                    # let's assume that we can just add blocks split among pieces
                    # rather than average among pieces
                    if d.from_id in one_round_ago.keys():
                        one_round_ago[d.from_id] += d.blocks
                    else:
                        one_round_ago[d.from_id] = d.blocks
            requester_ids = [r.requester_id for r in requests]
            logging.debug("Here are the people who gave to me last round: %s", one_round_ago.keys())
            logging.debug("Here are the people who requested from me this round: %s", requester_ids)
            valid_peers = set(one_round_ago.keys()).intersection(set(requester_ids))
            logging.debug("And here are the people who're in both!: %s", valid_peers)
            total_given = float(sum(one_round_ago[i] for i in valid_peers))

            chosen = list(valid_peers)
            bws = [((one_round_ago[i] / total_given) * 0.9 * self.up_bw) for i in chosen]
            optimistic = random.choice(requester_ids)
            # make sure we're not optimistically picking someone who already deserves it
            # but do give up if everyone already happens deserves it
            while optimistic in chosen and set(chosen) != set(requester_ids):
                optimistic = random.choice(requester_ids)
            if optimistic not in chosen:
                chosen.append(optimistic)
                bws.append(0.1 * self.up_bw)
            logging.debug("Here's who I've ultimately chosen: %s", chosen)
            logging.debug("And here's how much I've allotted to each: %s", bws)

            # request = random.choice(requests)
            # chosen = [request.requester_id]
            # Evenly "split" my upload bandwidth among the one chosen requester
            # bws = even_split(self.up_bw, len(chosen))

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(chosen, bws)]

        return uploads
