import user
from user import User
import copy

def iter_da_within_group(people, people_ids, target_min, matches):
    #form initial preference lists
    for u in people:
        u.temp_prefs = []
        for user_id in u.prefs:
            if user_id in people_ids:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) #represents not getting matched

    #duplicate the users
    propose = copy.deecopy(people)
    receive = copy.deepcopy(people)
    propose_dict = map_users_list_to_dict(propose)
    receive_dict = map_users_list_to_dict(receive)

    for i in range((target_min + 1) / 2):
        still_unmatched_proposers = True
        while (still_unmatched_proposers):

            #do proposing
            for u in propose:
                if u.current_match is None:
                    target_id = u.temp_prefs[u.prop_pos]
                    if target_id == 0:
                        #not getting matched this round
                        u.current_match = 0
                    else:
                        target = receive_dict[target_id]
                        u.prop_pos += 1
                        if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                            #accept the proposal
                            if target.current_match is not None:
                                propose_dict[target.current_match].current_match = None
                            u.current_match = target.id
                            target.current_match = u.id
                            target.rec_rank = target.temp_prefs.index(u.id)

            #check if any proposers are still unmatched
            still_unmatched_proposers = False
            for u in propose:
                if u.current_match is None:
                    still_unmatched_proposers = True
                    break

        #add matches from this round to master matches list
        #remove this round's match from preference list
        #reset user fields for next iteration
        for u in propose:
            if u.current_match != 0:
                matches[u.id].append(u.current_match)
                u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if (u.current_match is not None) and (matches[u.id][-1] != u.current_match):
                matches[u.id].append(u.current_match)
            if (u.current_match is not None):
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

    return matches

def iter_da_between_groups(proposer, propose_ids, receiver, receive_ids, target_min, matches):
    propose = copy.deepcopy(proposer)
    receive = copy.deepcopy(receiver)
    propose_dict = map_users_list_to_dict(propose)
    receive_dict = map_users_list_to_dict(receive)

    #form initial preference lists
    for u in propose:
        u.temp_prefs = []
        for user_id in u.prefs:
            if user_id in receive_ids:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) #represents not getting matched
    for u in receive:
        u.temp_prefs = []
        for user_id in u.prefs:
            if user_id in propose_ids:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) #represents not getting matched

    #consider relative sizes of propose & receive sides
    larger = propose #shallow copy
    smaller = receive #shallow copy
    propose_is_larger = True
    if (len(receive_ids) > len(propose_ids)):
        larger = receive #shallow copy
        smaller = propose #shallow copy
        propose_is_larger = False
    #larger_size = max(len(propose_ids), len(receive_ids))
    #smaller_size = min(len(propose_ids), len(receive_ids))

    #assign number of matches before dropping out
    for u in larger:
        u.matches_needed = target_min

    #########################
    need_more_matches = True
    while need_more_matches:

        still_unmatched_proposers = True
        while (still_unmatched_proposers):

            #do proposing
            for u in propose:
                if u.dropped_out:
                    continue

                if u.current_match is None:
                    target_id = None
                    while True:
                        target_id = u.temp_prefs[u.prop_pos]
                        if target_id == 0:
                        #not getting matched this round
                            u.current_match = 0
                        u.prop_pos += 1
                        if not receive_dict[target_id].dropped_out:
                            #found a valid target id
                            break

                    target = receive_dict[target_id]
                    if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                        #accept the proposal
                        if target.current_match is not None:
                            propose_dict[target.current_match].current_match = None
                        u.current_match = target.id
                        target.current_match = u.id
                        target.rec_rank = target.temp_prefs.index(u.id)

            #check if any proposers are still unmatched
            still_unmatched_proposers = False
            for u in propose:
                if u.dropped_out:
                    continue

                if u.current_match is None:
                    still_unmatched_proposers = True
                    break

        #update matches_needed for bigger side
        #check if any user still needs more matches
        #flag any users that are dropping out
        need_more_matches = False
        for u in bigger:
            if (u.current_match is not None) and (u.current_match != 0):
                u.matches_needed -= 1
            if u.matches_needed > 0:
                need_more_matches = True
            else:
                u.dropped_out = True

        #add matches from this round to master matches list
        #remove this round's match from preference list
        #reset user fields for next iteration
        for u in propose:
            if u.current_match != 0:
                matches[u.id].append(u.current_match)
                u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if (u.current_match is not None) and (matches[u.id][-1] != u.current_match):
                matches[u.id].append(u.current_match)
            if (u.current_match is not None):
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

    return matches

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

    #define parameters
    overall_target_min = 10
    mixing_ratio = 0.5

    #set up dictionary to hold everyone's matchings
    #divide population into particular groups
    #record ids for different groups
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

    #call the iterated DA functions in 6 stages
    print "Computing matchings for homosexual & bisexual males..."
    matches = iter_da_within_group((homo_male + bi_male), (homo_m_id + bi_m_id), (overall_target_min * mixing_ratio), matches)
    print "Computing matchings for homosexual & bisexual females..."
    matches = iter_da_within_group((homo_female + bi_female), (homo_f_id + bi_f_id), (overall_target_min * mixing_ratio), matches)
    print "Computing matchings for homosexual males..."
    matches = iter_da_within_group(homo_male, homo_m_id, (overall_target_min * (1.0 - mixing_ratio)), matches)
    print "Computing matchings for homosexual females..."
    matches = iter_da_within_group(homo_female, homo_f_id, (overall_target_min * (1.0 - mixing_ratio)), matches)
    print "Computing matchings for bisexual & heterosexual males & females..."
    matches = iter_da_between_groups((heter_male + bi_male), (heter_m_id + bi_m_id), (heter_female + bi_female), (heter_f_id + bi_f_id), (overall_target_min * (1.0 - mixing_ratio)), matches)
    print "Computing matchings for heterosexual males & females..."
    matches = iter_da_between_groups(heter_male, heter_m_id, heter_female, heter_f_id, (overall_target_min * mixing_ratio), matches)

    #create ranked list for each person by sorting their matches
    sort_all_match_lists(matches, users_dict)

    #check on how many matches people actually have
    analyze_num_matches(matches, users_dict)

    #check the utility values from rank perspective and distance perspective -- in two separate functions
    analyze_rank_utility(matches, users_dict)
    analyze_distance_utility(matches, users_dict)

run_iter_da_for_all()
