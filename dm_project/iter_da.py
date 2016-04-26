# here's a boilerplate algorithm for the iterated deferred acceptance

import user
from user import User


# maybe run a single round of DA here?
# and maybe return list of matches by user index?
# or maybe a dict of matches by user?
def one_round_iter_da():
    pass


# maybe run da on two groups of users, like HoM+BiM w/ itself
# or HeM+BiM -- HeF+BiF?
# could run multiple rounds?
def iter_da_on_group():
    pass


# return matches on all users
# just dummy code for now
def run_iter_da_for_all():
    users = user.gen_users(10)
    users = user.add_prefs(users)
    for u in users:
        print "id: %d, prefs: %s" % (u.id, u.prefs)

run_iter_da_for_all()
