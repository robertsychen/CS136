import user
from user import User
import copy

def iter_da_within_group(people, people_ids, people_min, people_max, matches, all_users_ids):
    # precompute whether each user is within this group of people
    group_dict = {}
    for u_id in all_users_ids:
        group_dict[u_id] = False
    for u_id in people_ids:
        group_dict[u_id] = True

    # form initial preference lists
    for u in people:
        u.temp_prefs = []
        for user_id in u.prefs:
            if group_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched

    # duplicate the users
    propose = copy.deepcopy(people)
    receive = copy.deepcopy(people)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)

    # dictionary for how many matches have been obtained: shared between propose and receive
    matches_obtained = {}
    for u_id in people_ids:
        matches_obtained[u_id] = 0

    #dictionary for whether dropped out: shared between propose and receive
    dropped_out = {}
    for u_id in people_ids:
        dropped_out[u_id] = False

    need_more_matches = True
    while (need_more_matches):
        print "new iteration"

        still_unmatched_proposers = True

        while (still_unmatched_proposers):
            # do proposing
            for u in propose:
                if dropped_out[u.id]:
                    continue

                if u.current_match is None:
                    target_id = None
                    while True:
                        target_id = u.temp_prefs[u.prop_pos]
                        if target_id == 0:
                        # not getting matched this round
                            u.current_match = 0
                            break
                        u.prop_pos += 1

                        if not dropped_out[target_id]:
                            # found a valid target id
                            break

                    if target_id != 0:
                        target = receive_dict[target_id]

                        if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                            # accept the proposal
                            if target.current_match is not None:
                                propose_dict[target.current_match].current_match = None
                            u.current_match = target.id
                            target.current_match = u.id
                            target.rec_rank = target.temp_prefs.index(u.id)

            # check if any proposers are still unmatched
            still_unmatched_proposers = False
            for u in propose:
                if dropped_out[u.id]:
                    continue

                if u.current_match is None:
                    still_unmatched_proposers = True
                    break

        # add matches from this round to master matches list
        # remove this round's match from preference list
        # reset user fields for next iteration
        for u in propose:
            if dropped_out[u.id]:
                continue
            if u.current_match != 0:
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    matches_obtained[u.id] += 1
                if u.current_match is not None:
                    u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if dropped_out[u.id]:
                continue
            if (u.current_match is not None):
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    matches_obtained[u.id] += 1
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

        # check if any user still needs more matches
        # flag any users that are dropping out
        need_more_matches = False
        for u in propose:
            print matches_obtained[u.id]
            if matches_obtained[u.id] < people_min:
                need_more_matches = True
            elif matches_obtained[u.id] >= people_max:
                dropped_out[u.id] = True
    return matches


def iter_da_between_groups(proposer, propose_ids, receiver, receive_ids, prop_min, rec_min, prop_max, rec_max, matches, all_users_ids):
    propose = copy.deepcopy(proposer)
    receive = copy.deepcopy(receiver)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)

    prop_dict = {}
    for u_id in all_users_ids:
        prop_dict[u_id] = False
    for u_id in propose_ids:
        prop_dict[u_id] = True
    rec_dict = {}
    for u_id in all_users_ids:
        rec_dict[u_id] = False
    for u_id in receive_ids:
        rec_dict[u_id] = True

    # form initial preference lists
    for u in propose:
        u.temp_prefs = []
        for user_id in u.prefs:
            if rec_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched
    for u in receive:
        u.temp_prefs = []
        for user_id in u.prefs:
            if prop_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched

    # consider relative sizes of propose & receive sides
    #larger = propose # shallow copy
    #smaller = receive # shallow copy
    #propose_is_larger = True
    #if (len(receive_ids) > len(propose_ids)):
    #    larger = receive # shallow copy
    #    smaller = propose # shallow copy
    #    propose_is_larger = False

    # assign number of matches so far
    for u in propose:
        u.matches_obtained = 0
    for u in receive:
        u.matches_obtained = 0

    need_more_matches = True
    while need_more_matches:
        print "new iteration"
        # start new iteration of DA
        still_unmatched_proposers = True
        while (still_unmatched_proposers):
            # do proposing
            for u in propose:
                if u.dropped_out:
                    continue

                if u.current_match is None:
                    target_id = None
                    while True:
                        target_id = u.temp_prefs[u.prop_pos]
                        if target_id == 0:
                        # not getting matched this round
                            u.current_match = 0
                            break
                        u.prop_pos += 1

                        if not receive_dict[target_id].dropped_out:
                            # found a valid target id
                            break

                    if target_id != 0:
                        target = receive_dict[target_id]

                        if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                            # accept the proposal
                            if target.current_match is not None:
                                propose_dict[target.current_match].current_match = None
                            u.current_match = target.id
                            target.current_match = u.id
                            target.rec_rank = target.temp_prefs.index(u.id)

            # check if any proposers are still unmatched
            still_unmatched_proposers = False
            for u in propose:
                if u.dropped_out:
                    continue

                if u.current_match is None:
                    still_unmatched_proposers = True
                    break

        # add matches from this round to master matches list
        # remove this round's match from preference list
        # reset user fields for next iteration
        # update matches_needed for bigger side
        for u in propose:
            if u.dropped_out:
                continue
            if u.current_match != 0:
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    u.matches_obtained += 1
                if u.current_match is not None:
                    u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if u.dropped_out:
                continue
            if (u.current_match is not None):
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    u.matches_obtained += 1
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

        # check if any user still needs more matches
        # flag any users that are dropping out
        need_more_matches = False
        for u in propose:
            if u.matches_obtained < prop_min:
                need_more_matches = True
                #print "prop" + str(u.matches_obtained)
            elif u.matches_obtained >= prop_max:
                u.dropped_out = True
        for u in receive:
            if u.matches_obtained < rec_min:
                need_more_matches = True
                #print "rec" + str(u.matches_obtained)
            elif u.matches_obtained >= rec_max:
                u.dropped_out = True

    return matches

# return matches on all users
def run_iter_da_for_all():

    # random users or actual datamatch users?
    # users = user.gen_users(1000)
    # users = user.add_prefs(users)
    users = user.load_users('anon_data_2016.txt')
    users = user.load_features(users, 'features_2016.txt')
    # if no prefs exist yet, calculate; otherwise, load
    # users = user.calc_prefs(users)
    users = user.load_prefs(users, 'preferences_2016.txt')
    users = user.filter_prefs(users)

    users_dict = user.map_users_list_to_dict(users)
    all_users_ids = users_dict.keys()

    # define parameters
    mixing_ratio = 0.5

    overall_female_min = 10
    overall_male_min = 1
    overall_within_group_min = 10

    dropout_female_factor = 1.2
    dropout_male_factor = 18.0
    dropout_within_group_factor = 1.5

    '''
    GROUPING
    Sort users into preference groups
    Record ids for each group
    Set up dictionary to hold everyone's matchings
    '''

    matches = {}
    homo_male = []
    homo_female = []
    heter_male = []
    heter_female = []
    bi_male = []
    bi_female = []
    homo_m_id = []
    homo_f_id = []
    heter_m_id = []
    heter_f_id = []
    bi_m_id = []
    bi_f_id = []
    for u in users:
        matches[u.id] = []
        if u.gender == 0:
            if u.seeking == 0:
                homo_male.append(u)
                homo_m_id.append(u.id)
            elif u.seeking == 1:
                heter_male.append(u)
                heter_m_id.append(u.id)
            else:
                bi_male.append(u)
                bi_m_id.append(u.id)
        else:
            if u.seeking == 0:
                heter_female.append(u)
                heter_f_id.append(u.id)
            elif u.seeking == 1:
                homo_female.append(u)
                homo_f_id.append(u.id)
            else:
                bi_female.append(u)
                bi_f_id.append(u.id)

    
    #print len(homo_m_id)
    #print len(bi_m_id)
    #print len(homo_f_id)
    #print len(bi_f_id)
    #print len(heter_m_id)
    #print len(heter_f_id)
    

    # temporarily truncate for test reasons
    #heter_male = heter_male[:163]
    #heter_female = heter_female[:199]
    #heter_m_id = heter_m_id[:163]
    #heter_f_id = heter_f_id[:199]

    '''
    ITERATED DA
    Find matches in 6 stages
    '''
    print "Computing matchings for homosexual & bisexual males..."
    min_target = (overall_within_group_min * mixing_ratio)
    matches = iter_da_within_group((homo_male + bi_male), (homo_m_id + bi_m_id), min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual & bisexual females..."
    min_target = (overall_within_group_min * mixing_ratio)
    matches = iter_da_within_group((homo_female + bi_female), (homo_f_id + bi_f_id), min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual males..."
    min_target = (overall_within_group_min * (1.0 - mixing_ratio))
    matches = iter_da_within_group(homo_male, homo_m_id, min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual females..."
    min_target = (overall_within_group_min * (1.0 - mixing_ratio))
    matches = iter_da_within_group(homo_female, homo_f_id, min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for bisexual & heterosexual males & females..."
    min_target_female = (overall_female_min * (1.0 - mixing_ratio))
    min_target_male = (overall_male_min * (1.0 - mixing_ratio))
    #matches = iter_da_between_groups((heter_male + bi_male), (heter_m_id + bi_m_id), (heter_female + bi_female), (heter_f_id + bi_f_id), min_target_male, min_target_female, min_target_male * dropout_male_factor, min_target_female * dropout_female_factor, matches, all_users_ids)
    matches = iter_da_between_groups((heter_female + bi_female), (heter_f_id + bi_f_id), (heter_male + bi_male), (heter_m_id + bi_m_id), min_target_female, min_target_male, min_target_female * dropout_female_factor, min_target_male * dropout_male_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for heterosexual males & females..."
    min_target_female = (overall_female_min * (mixing_ratio))
    min_target_male = (overall_male_min * (mixing_ratio))
    #matches = iter_da_between_groups(heter_male, heter_m_id, heter_female, heter_f_id, min_target_male, min_target_female, min_target_male * dropout_male_factor, min_target_female * dropout_female_factor, matches, all_users_ids)
    matches = iter_da_between_groups(heter_female, heter_f_id, heter_male, heter_m_id, min_target_female, min_target_male, min_target_female * dropout_female_factor, min_target_male * dropout_male_factor, matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)

    # create ranked list for each person by sorting their matches
    user.sort_all_match_lists(matches, users_dict)
    
    print colored("Matching completed!", 'red', 'on_green', attrs=['bold'])
    
    # check on how many matches people actually have
    user.analyze_num_matches(matches, users_dict)

    for i in range(1, 4, 1):
        print '\033[95m#####################################'
        print 'TOP %s MATCHES' % i
        print '#####################################\033[0m'
        #check the utility values from rank perspective and distance perspective -- in two separate functions
        user.analyze_rank_utility(matches, users_dict, i)
        user.analyze_distance_utility(matches, users_dict, i)

run_iter_da_for_all()
