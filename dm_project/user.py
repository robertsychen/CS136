import random
import math
# for faster sorting on tuples
# see http://stackoverflow.com/questions/10695139/
# sort-a-list-of-tuples-by-2nd-item-integer-value
from operator import itemgetter
import numpy as np
import re
from termcolor import colored, cprint
from collections import OrderedDict

class User(object):

    num_features = 10
    genders = [0, 1]
    seekings = [0, 1, 2]
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
        self.temp_prefs = None # used in many-to-many and Iterated DA
        self.temp_pref_ranks = None # used in many-to-many DA
        self.prop_pos = 0 # used in Iterated DA: next person to propose to (for proposing side)
        self.current_match = None # used in Iterated DA
        self.match_list = [] # used in many-to-many DA
        self.rec_rank = None # used in Iterated DA: rank in temp_prefs for current_match (for receiving side)
        self.matches_obtained = None # used in Iterated DA
        self.quota = None # used in many-to-many DA
        self.dropped_out = False # used in Iterated DA

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

    # is compatible with other user?
    def is_compatibile(self, u):
        self_likes = ((u.gender == 0 and (self.seeking == 0 or self.seeking == 2)) or
                     (u.gender == 1 and (self.seeking == 1 or self.seeking == 2)))
        u_likes = ((self.gender == 0 and (u.seeking == 0 or u.seeking == 2)) or
                  (self.gender == 1 and (u.seeking == 1 or u.seeking == 2)))
        return (self_likes and u_likes)

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
# takes a looooong time because of the sorting/distance calculations
# thus the write to file option
def calc_prefs(users, save=True, compatible_only=False):
    for u1 in users:
        distances_and_ids = []
        for u2 in users:
            dist = u1.dist(u2) if (compatible_only and
                                   u1.is_compatibile(u2)) else -1
            if u2.id != u1.id:
                distances_and_ids += (u2.id, dist)
        distances_and_ids = [(u2.id, u1.dist(u2))
                             for u2 in users if u2.id != u1.id]
        distances_and_ids.sort(key=itemgetter(1))
        # print distances_and_ids
        u1.prefs = [u[0] for u in distances_and_ids]
        print '\rCalculated prefs for user %d: %s ....' % (u1.id, u1.prefs[0:5]),
    print colored("Calculated all preferences!", 'green', attrs=['bold'])
    if save:
        outfile = raw_input("Filename to save to prefs to?:")
        f = open(outfile, 'w')
        for u in users:
            f.write((str)(u.id) + ":")
            f.write(':'.join(map((str), u.prefs)))
            f.write('\n')
        f.close()
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
        u_gender = 0 if (u_details[3] == 'Male') else 1
        if u_details[4] == 'Men':
            u_seeking = 0
        elif u_details[4] == 'Women':
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


# load features from file and add to users
# file has format id:feature:feature:...
# returns array of users with features added
def load_features(users, filename):
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
        features = map((float), id_and_features[1:])
        users[u_index].features = features
    f.close()
    return users


def load_prefs(users, filename):
    f = open(filename)
    for line in f:
        id_and_prefs = line.split(':')
        # array index not guaranteed to equal id!!!
        # (but in general, since we sorted and users can only be missing
        # id should be lower than actual index; so we can speed up the search)
        u_id = (int)(id_and_prefs[0])
        u_index = min(len(users) - 1, u_id)
        while u_index >= 0:
            if users[u_index].id == u_id:
                break
            u_index -= 1
        prefs = map((int), id_and_prefs[1:])
        users[u_index].prefs = prefs
        print "\rLoaded preferences for user %d" % u_id,
    f.close()
    print colored("Loaded all preferences!", 'green', attrs=['bold'])
    return users


# handy for when you don't want to constantly have to look through the list...
# maps users in list to a dict, where dict key is user id and val is user
def map_users_list_to_dict(users):
    users_dict = {}
    for u in users:
        users_dict[u.id] = u
    return users_dict

def filter_prefs(users):
    users_dict = map_users_list_to_dict(users)
    for u in users:
        print "\rFiltering prefs for user %d" % u.id,
        u.prefs = filter(lambda x: u.is_compatibile(users_dict[x]), u.prefs)
    print colored("Filtering prefs done!", 'green', attrs=['bold'])
    return users

# takes dictionary of matches (with key = id, value = unsorted list of matches)
# and sorts all users' lists
# used at end of all stages to combine matches
def sort_all_match_lists(matches, users_dict):
    for key in matches:
        this_user = users_dict[key]
        temp_list = []
        for u_id in matches[key]:
            temp_list.append((this_user.dist(users_dict[u_id]), u_id))
        temp_list.sort()
        matches[key] = [x[1] for x in temp_list]
    return matches


# look at min, max, distribution of number of matches users have after running matching algorithm
# assumes matches is dictionary w/ key = id, value = list of matches
# returns dict of num matches histograms
def analyze_num_matches(matches, users_dict):
    num_matches = {}
    for s in User.seekings:
        num_matches[s] = {}
        for g in User.genders:
            num_matches[s][g] = []

    for u_id in matches:
        u = users_dict[u_id]
        num_matches[u.seeking][u.gender].append(len(matches[u_id]))

    def matches_str(seeking, gender):
        comb_num_matches = []
        seeking_array = [seeking] if isinstance( seeking, int ) else seeking
        gender_array = [gender] if isinstance( gender, int ) else gender
        for i in seeking_array:
            for j in gender_array:
                comb_num_matches += num_matches[i][j]
        return str(np.asarray(comb_num_matches).mean()) + ", " + \
            str({x: comb_num_matches.count(x) for x in set(comb_num_matches)})

    # print out mean, freq list for all match groups
    print colored('Mean, freq list of matches:', 'cyan', attrs=['bold'])
    print colored("Homo males: ", 'cyan') + matches_str(0, 0)
    print colored("Homo females: ", 'cyan') + matches_str(1, 1)
    print colored("Bi males: ", 'cyan') + matches_str(2, 0)
    print colored("Bi females: ", 'cyan') + matches_str(2, 1)
    print colored("Hetero males: ", 'cyan') + matches_str(1, 0)
    print colored("Hetero females: ", 'cyan') + matches_str(0, 1)
    print colored("All males: ", 'cyan') + matches_str([0, 1, 2], 0)
    print colored("All females: ", 'cyan') + matches_str([0, 1, 2], 1)
    print colored("All people: ", 'cyan') + matches_str([0, 1, 2], [0, 1])

    return num_matches

def analyze_rank_utility(matches, users_dict, k):

    print colored("Rank values:", 'cyan', attrs=['bold'])

    utilities = []
    for u_id in matches:
        prefs = users_dict[u_id].prefs
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append((prefs.index(v_id) + 1.0) / len(prefs))
            count += 1
            if count >= k:
                break
        utilities.append(np.mean(this_utility))
    print colored('For all users:', 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))

    # compute only for heterosexual males (to compare differences between two sides proposing)
    utilities = []
    for u_id in matches:
        if (users_dict[u_id].gender != 0) or (users_dict[u_id].seeking != 1):
            continue
        prefs = users_dict[u_id].prefs
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append((prefs.index(v_id) + 1.0) / len(prefs))
            count += 1
            if count >= k:
                break
        utilities.append(np.mean(this_utility))
    print colored("And for heterosexual males only:", 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))

    # compute only for heterosexual females (to compare differences between two sides proposing)
    utilities = []
    for u_id in matches:
        if (users_dict[u_id].gender != 1) or (users_dict[u_id].seeking != 0):
            continue
        prefs = users_dict[u_id].prefs
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append((prefs.index(v_id) + 1.0) / len(prefs))
            count += 1
            if count >= k:
                break
        utilities.append(np.mean(this_utility))
    print colored("And for heterosexual females only:", 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))

def analyze_distance_utility(matches, users_dict, k):
    print colored("Distance values:", 'cyan', attrs=['bold'])

    utilities = []
    for u_id in matches:
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append(users_dict[u_id].dist(users_dict[v_id]))
            count += 1
            if count >= k:
                break

        utilities.append(np.mean(this_utility))
    print colored('For all users:', 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))

    # compute only for heterosexual males (to compare differences between two sides proposing)
    utilities = []
    for u_id in matches:
        if (users_dict[u_id].gender != 0) or (users_dict[u_id].seeking != 1):
            continue
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append(users_dict[u_id].dist(users_dict[v_id]))
            count += 1
            if count >= k:
                break
        utilities.append(np.mean(this_utility))
    print colored("And for heterosexual males only:", 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))

    # compute only for heterosexual females (to compare differences between two sides proposing)
    utilities = []
    for u_id in matches:
        if (users_dict[u_id].gender != 1) or (users_dict[u_id].seeking != 0):
            continue
        this_utility = []
        count = 0
        for v_id in matches[u_id]:
            this_utility.append(users_dict[u_id].dist(users_dict[v_id]))
            count += 1
            if count >= k:
                break
        utilities.append(np.mean(this_utility))
    print colored("And for heterosexual females only:", 'cyan'),
    print "Min av.: %s, mean av.: %s, max av.: %s" % (str(round(min(utilities), 6)),
        str(round(np.mean(utilities), 6)), str(round(max(utilities), 6)))
