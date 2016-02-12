We can move this to TeX later, if need be

# Analysis
1. For the standard client explain what assumptions or decisions you had to make beyond
those specified in Chapter 5.

  Let's start with the requests, which had fewer assumptions.
  * When we say "rarest" we count excluding ourselves. This is
    probably the easiest assumption, since we're not going to
    be requesting pieces we have anyway.
  * We request as many as possible from each peer; the difference
    from the dummy is that we just use our bandwidth to request
    rarest pieces rather than random ones. This assumption is
    mainly for ease of implementation rather than theory:
    there's not going to be much way in the reference client
    to handle making sure you don't request the same piece
    from multiple clients, so we might as well just ask outright.
    We could implement that...but then we're not really making
    a reference client anymore.  

  And now for uploads.  
  * When we say "highest average download rate" we merely
    add number of blocks downloaded, rather than dividing
    evenly among multiple pieces from the same peer. I think
    this is a fair implementation, and doing otherwise would
    have negligible effect. Furthermore, we choose two rounds,
    as a nice sliding average.
  * We'll give to our "Best Friends" i.e. our top three slots
    over the last two rounds, even if they didn't request from
    us. We also won't find new/additional friends--we don't want to
    accidentally promote selfishness by giving to someone who
    doesn't deserve it. The principle here is to promote consistent friendship :)
  * Again, assume that the optimistic unlock doesn't have to be among
    the people who requested from us. We don't want to be taken
    advantage of.
  * Let's assume that if the optimistic happens to already be
    among our best friends that we can just wait for our best
    friends to change, or for the optimistic to change, rather
    than giving more to that peer. We might as well be fair,
    to prevent over-reliance in friendship.

2. ()
# Theory
1. State three ways in which the peer-to-peer le sharing game of the BitTorrent network is different from a repeated Prisoner's dilemma.

  * Peers have more than two actions! They can vary the amount of bandwidth to give to each peer, for example.
  * The neighborhood of peers is much larger than just two players, as in IPD--the amount of bandwidth one peer
    receives from another depends both on the latter peer and the entire neighborhood of peers.
  * A peer may no longer want any pieces from a certain peer, ending their relationship prematurely.

2. State three ways in which the BitTorrent reference client is dierent from the tit-for-tat strategy in a repeated Prisoner's Dilemma.

  * There's optimistic unlocking! This is equivalent to randomly forgiving and resetting the game in tit-for-tat.
  * There are a set number of spots that are being competed for, rather than a single other peer. This leads to
    more of an "auction" model than an a single 2-player game.
  * The reference client might not immediately download from its current "friend," since it wants to find the rarest pieces
    first. Thus, while cooperation in general is still encouraged, the client might lose its favored status by
    reaching for rare pieces first.
