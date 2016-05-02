import re
import user
from user import User

#take 2016 matches txt file and convert into data structure for matches: dictionary of users' ids & ranked list of ids of their matches
def format_2016_matches(filename):
    matches = {}
    f = open(filename)
    for line in f:
        match_info = re.split(':|,', line)
        this_id = int(match_info[0])
        this_matches = []
        for i in range(1,len(match_info)):
            if i % 2 == 1:
                this_matches.append(int(match_info[i]))
        matches[this_id] = this_matches
    return matches

def analyze_2016_algo():
    users = user.load_users('anon_data_2016.txt')
    users = user.load_features(users, 'features_2016.txt')
    users = user.load_prefs(users, 'preferences_2016.txt')

    users_dict = user.map_users_list_to_dict(users)

    #deal with yucky special case
    matches = format_2016_matches('matches_2016.txt')
    for u_id in matches:
        if (3148 in matches[u_id]):
            matches[u_id].remove(3148)
    del matches[3148]


    #check on how many matches people actually have
    user.analyze_num_matches(matches, users_dict)

    #check the utility values from rank perspective and distance perspective
    user.analyze_rank_utility(matches, users_dict)
    user.analyze_distance_utility(matches, users_dict)

analyze_2016_algo()


#NOTE: either match up the # of matches well or else be sure to normalize in some appropriate way as far as diff. # of matches in our methods vs. 2016 method
