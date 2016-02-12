#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers 
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

from __future__ import division
import random
import logging
from messages import Upload, Request
from peer import Peer
from collections import Counter
import itertools


class A000Tyrant(Peer):
    num_download_rate_average_rounds = 2
    alpha = 1.2
    gamma = 0.9
    r = 2

    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.past_peer_finish_rates = {}
        self.past_peer_download_rates = []
        self.past_peer_upload_rates = []
        self.peer_download_rates = {}
        self.peer_upload_rates = {}

    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """

        needed_pieces = set(i for i in xrange(len(self.pieces)) if self.pieces[i] < self.conf.blocks_per_piece)
        logging.debug("Needed pieces: %s" % needed_pieces)

        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        pieces_frequency = Counter(itertools.chain(*(p.available_pieces for p in peers)))

        requests = []  # We'll put all the things we want here

        # request all available pieces from all peers!
        # (up to self.max_requests from each)
        for peer in peers:
            available_pieces = set(peer.available_pieces)
            downloadable_pieces = list(available_pieces.intersection(needed_pieces))
            # Do a weighted shuffle so that rare pieces are more likely to be at the front
            downloadable_pieces.sort(key=lambda x: random.random() * pieces_frequency[x])
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            for piece_id in downloadable_pieces:
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                start_block = self.pieces[piece_id]
                r = Request(self.id, peer.id, piece_id, start_block)
                requests.append(r)

        logging.debug("Requests: %s" % requests)

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

        previous_peer_download_rates = Counter()
        if history.downloads:
            for d in history.downloads[-1]:
                previous_peer_download_rates[d.from_id] += d.blocks
        self.past_peer_download_rates.append(previous_peer_download_rates)

        previous_peer_upload_rates = {}
        if history.uploads:
            for u in history.uploads[-1]:
                previous_peer_upload_rates[u.to_id] = u.bw
        self.past_peer_upload_rates.append(previous_peer_upload_rates)

        for p in peers:
            # Keep track of piece finish rate
            available_pieces = set(p.available_pieces)
            if p.id not in self.past_peer_finish_rates:
                incremental_piece_count = [len(p.available_pieces)]
                self.past_peer_finish_rates[p.id] = (available_pieces, incremental_piece_count)
            else:
                previous_pieces, incremental_piece_count = self.past_peer_finish_rates[p.id]
                incremental_piece_count = incremental_piece_count + [len(available_pieces - previous_pieces)]
                self.past_peer_finish_rates[p.id] = (available_pieces, incremental_piece_count)

            # Determine download rates
            if p.id in previous_peer_download_rates:
                peer_download_rate = previous_peer_download_rates[p.id]
                # Downloaded from peer in the previous round, set to actual download rate
                self.peer_download_rates[p.id] = peer_download_rate
            else:
                # Estimate download rate from piece finish rate
                past_piece_finish_rates = incremental_piece_count[-self.num_download_rate_average_rounds:]
                peer_download_rate = float(sum(past_piece_finish_rates)) * self.conf.blocks_per_piece / len(
                    past_piece_finish_rates)
                self.peer_download_rates[p.id] = peer_download_rate

            # Determine upload rates needed to satisfy peers to unchoke us
            if p.id in previous_peer_upload_rates:
                # Peer was unchoked by us in the previous period
                if p.id not in previous_peer_download_rates:
                    # Peer did not unchoke us
                    self.peer_upload_rates[p.id] *= self.alpha
                elif len(self.past_peer_upload_rates) >= self.r:
                    # Check if peer unchoked us in the previous r periods
                    unchoked = True
                    for ur in self.past_peer_upload_rates[-self.r:]:
                        if p.id not in ur:
                            unchoked = False
                            break
                    if unchoked:
                        self.peer_upload_rates[p.id] *= self.gamma
            else:
                # Estimate upload rate with equal split
                self.peer_upload_rates[p.id] = peer_download_rate

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            return []
        else:
            peer_request_bw = Counter()
            for r in requests:
                peer_request_bw[r.requester_id] += self.conf.blocks_per_piece - r.start

            logging.debug("Past peer finish rates %s" % self.past_peer_finish_rates)
            logging.debug("Past peer upload rates %s" % self.past_peer_upload_rates)
            logging.debug("Past peer download rates %s" % self.past_peer_download_rates)
            logging.debug("Upload rates: %s" % self.peer_upload_rates)
            logging.debug("Download rates: %s" % self.peer_download_rates)

            peer_ids = list(peer_request_bw.keys())
            peer_ids.sort(key=lambda x: self.peer_download_rates[x] / self.peer_upload_rates[x]
                          if self.peer_download_rates[x] > 0 and self.peer_upload_rates[x] > 0
                          else 1.0)

            uploads = []

            remaining_bw = self.up_bw
            for peer_id in peer_ids:
                upload_bw = min(peer_request_bw[peer_id], self.peer_upload_rates[peer_id])
                if remaining_bw >= upload_bw:
                    uploads.append(Upload(self.id, peer_id, upload_bw))
                    remaining_bw -= upload_bw
                else:
                    break

            return uploads
