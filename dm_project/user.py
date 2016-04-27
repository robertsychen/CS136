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

    # index in any array is not the same as ID!!!
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

    # euclidean distance on features vector
    def dist(self, u):
        d_squares = 0
        for i in range(User.num_features):
            d_squares += abs(pow(self.features[i], 2) - pow(u.features[i], 2))
        return math.sqrt(d_squares)

    # is gender compatible with other user?
    def is_compatibile(self, u):
        return (u.gender == 0 and (self.seeking == 0 or self.seeking == 2) or
                u.gender == 1 and (self.seeking == 1 or self.seeking == 2))


# generate and return n random users
# no preference ordering yet
def gen_users(n):
    users = [None] * n
    for i in xrange(n):
        f = [random.random() for _ in range(User.num_features)]
        users[i] = User(i, f, random.randint(0, 1),
                        random.randint(0, 2), [])
    return users


# calculate, sort, and insert preferences on all users
# returns the list of users again
def add_prefs(users, compatible_only=False):
    for u1 in users:
        distances_and_ids = []
        for u2 in users if u2.id != u1.id:
            dist = u1.dist(u2) if (compatible_only and
                                   u1.is_compatibile(u2)) else -1
            distances_and_ids += (u2.id, dist)
        distances_and_ids = [(u2.id, u1.dist(u2))
                             for u2 in users if u2.id != u1.id]
        distances_and_ids.sort(key=itemgetter(1))
        # print distances_and_ids
        u1.prefs = [u[0] for u in distances_and_ids]
        print 'Loaded prefs for user %d: %s ....' % (u1.id, u1.prefs[0:5])
    return users


# load users from filename
# assumes 2016 format id:year:house:email:gender:seeking:matches
# we can ignore everything except year, gender, and seeking
# returns typical users matrix
def load_users(filename):
    f = open(filename)
    num_users = sum(1 for line in f)
    users = [None] * num_users
    # don't forget to reset the seek...
    f.seek(0)
    i = 0
    for line in f:
        # get user details
        u_details = line.split(':')
        u_id = (int)(u_details[0])
        u_gender = 0 if (u_details[4] == 'Male') else 1
        if u_details[5] == 'Men':
            u_seeking = 0
        elif u_details[5] == 'Women':
            u_seeking = 1
        else:
            u_seeking = 2
        # create user
        users[i] = User(u_id, [], u_gender, u_seeking, [])
        # user ids not in order in file!
        i += 1
    # and do a bit of processing just for ease of use...
    users.sort(key=lambda u: u.id)
    f.close()
    return users


def add_features_to_users(users, filename):
    f = open(filename)
    for line in f:
        id_and_features = line.split(':')
        # array index not guaranteed to equal id!!!
        # (but in general, since we sorted and users can only be missing
        # id should be lower than actual index; so we can speed up the search)
        u_id = (int)(id_and_features[0])
        u_index = min(len(users) - 1, u_id)
        while u_index >= 0:
            if users[u_index].id == u_id:
                break
            u_index -= 1
        features = map((float), id_and_features[1:-1])
        users[u_index].features = features
    f.close()
    return users
