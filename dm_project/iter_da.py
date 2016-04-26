# here's a boilerplate algorithm for the iterated deferred acceptance

import user
from user import User


# return matches
def run_da():
    users = user.gen_users(10)
    users = user.add_prefs(users)
    for u in users:
        print "id: %d, prefs: %s" % (u.id, u.prefs)

run_da()
