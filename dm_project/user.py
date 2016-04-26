import random
import math
# for faster sorting on tuples
# see http://stackoverflow.com/questions/10695139/
# sort-a-list-of-tuples-by-2nd-item-integer-value
from operator import itemgetter


class User(object):

    num_features = 10
    # lazily define some constants for gender and seeking
    # 0 = male, 1 = female
    # 0 = male, 1 = female, 2 = both

    def __init__(self, id, features, gender, seeking, prefs):
        self.id = id
        self.features = features
        self.gender = gender
        self.seeking = seeking
        self.prefs = prefs

    def __str__(self):
        return "id: %d, features: %s, gender: %d, seeking: %d, prefs: %s" % (
            self.id, self.features, self.gender, self.seeking, self.prefs
        )

    def dist(self, u):
        d_squares = 0
        for i in range(User.num_features):
            d_squares += abs(pow(self.features[i], 2) - pow(u.features[i], 2))
        return math.sqrt(d_squares)


# generate and return n random users
def gen_users(n):
    users = [None] * n
    for i in xrange(n):
        f = [random.random() for _ in range(User.num_features)]
        users[i] = User(i, f, random.randint(0, 1),
                        random.randint(0, 2), [])
    return users


# calculate, sort, and insert preferences on all users
def add_prefs(users):
    for u1 in users:
        distances_and_ids = [(u2.id, u1.dist(u2))
                             for u2 in users if u2.id != u1.id]
        distances_and_ids = sorted(distances_and_ids, key=itemgetter(1))
        print distances_and_ids
        u1.prefs = [u[0] for u in distances_and_ids]
    return users
