# here's a boilerplate algorithm for the iterated deferred acceptance

#hello world

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
    # users = user.gen_users(10)
    # users = user.add_prefs(users)
    users = user.load_users('anon_data_2016.txt')
    users = user.load_features(users, 'features_2016.txt')
    # users = user.calc_prefs(users)
    users = user.load_prefs(users, 'preferences_2016.txt')
    users_dict = user.map_users_list_to_dict(users)
    print "id: %d, prefs: %s" % (users[0].id, users[0].prefs[0:10])
    for u in users[0].prefs[0:40]:
        print "id: %d, dist: %s" % (u, users[0].dist(users_dict[u]))

run_iter_da_for_all()
