import re
import user
from user import User
from termcolor import colored, cprint

# take 2016 matches txt file and convert into data structure for matches: dictionary of users' ids & ranked list of ids of their matches
def format_2016_matches(filename):
    matches = {}
    f = open(filename)
    line_num = 0
    for line in f:
        print "\rLoading match line %d" % line_num,
        match_info = re.split(':|,', line)
        this_id = int(match_info[0])
        this_matches = []
        for i in range(1,len(match_info)):
            if i % 2 == 1:
                this_matches.append(int(match_info[i]))
        matches[this_id] = this_matches
        line_num += 1
    print colored("Loaded all matches!", 'green', attrs=['bold'])
    return matches

def analyze_2016_algo():

    # real users
    # users = user.load_users('anon_data_2016.txt')
    # users = user.load_features(users, 'features_2016.txt')
    # users = user.load_prefs(users, 'preferences_2016.txt')
    # users = user.filter_prefs(users)
    #
    # users_dict = user.map_users_list_to_dict(users)
    #
    # matches = format_2016_matches('matches_2016.txt')
    # for u_id in matches:
    #     if (3148 in matches[u_id]):
    #         matches[u_id].remove(3148)
    #
    # del matches[3148]

    # or saved random users
    users = user.load_users('random_data_1500.txt')
    users = user.load_features(users, 'random_features_1500.txt')
    users = user.load_prefs(users, 'random_prefs_1500.txt')
    users = user.filter_prefs(users)
    users_dict = user.map_users_list_to_dict(users)
    matches = format_2016_matches('ip_matches_1500_real_False.txt')

    # double check that we have a valid match set
    for u in matches.keys():
        for m in matches[u]:
            assert(users_dict[u].is_compatibile(users_dict[m]))

    user.sort_all_match_lists(matches, users_dict)
    # check on how many matches people actually have
    user.analyze_num_matches(matches, users_dict)

    for i in range(1, 4, 1):
        print '\033[95m#####################################'
        print 'TOP %s MATCHES' % i
        print '#####################################\033[0m'
        #check the utility values from rank perspective and distance perspective -- in two separate functions
        user.analyze_rank_utility(matches, users_dict, i)
        user.analyze_distance_utility(matches, users_dict, i)

analyze_2016_algo()


# note: need to write function to compute utility for matches_2016.txt
# be sure to normalize in some appropriate way as far as diff. # of matches in our methods vs. 2016 method
