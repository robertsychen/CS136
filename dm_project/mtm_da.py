from __future__ import division

import user
from user import User
import copy
import math
import bisect
import random

def mtm_da_within_group(people, people_ids, target_min, matches, all_users_ids):
    #precompute whether each user is within this group of people
    group_dict = {}
    for u_id in all_users_ids:
        group_dict[u_id] = False
    for u_id in people_ids:
        group_dict[u_id] = True

    #form initial preference lists
    for u in people:
        u.temp_prefs = []
        u.temp_pref_ranks = {}
        rank = 1
        for user_id in u.prefs:
            if group_dict[user_id]:
                u.temp_prefs.append(user_id)
                u.temp_pref_ranks[user_id] = rank
                rank += 1

    #duplicate the users
    propose = receive = copy.deepcopy(people)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)
        
    while True:
        # proposal phase
        for u in propose:
            # propose until quota is reached
            while len(u.match_list) < target_min and u.prop_pos < len(u.temp_prefs):
                receiver_id = u.temp_prefs[u.prop_pos]
                receiver = receive_dict[receiver_id]
                    
                r_rank = u.temp_pref_ranks[receiver_id]
                elem = (r_rank, receiver_id)
                if elem not in u.match_list:
                    # insert in sorted order
                    bisect.insort_left(u.match_list, elem)
                
                u.prop_pos += 1
                
                u_rank = receiver.temp_pref_ranks[u.id]
                elem = (u_rank, u.id)
                if elem not in receiver.match_list:
                    # insert in sorted order
                    bisect.insort_left(receiver.match_list, elem)
                
        # accept/reject phase
        for u in receive:
            # reject until match list size is within quota
            while len(u.match_list) > target_min:
                # remove last element from match list
                rank, proposer_id = u.match_list.pop()
                proposer = propose_dict[proposer_id]
                
                # unmatch user
                u_rank = proposer.temp_pref_ranks[u.id]
                proposer.match_list.remove((u_rank, u.id))
                
        # check if finished
        finished = True
        for u in propose:
            if len(u.match_list) < target_min and u.prop_pos < len(u.temp_prefs):
                finished = False
                break
                
        if finished:
            # end the algorithm
            break
        
    for u in receive:
        for rank, id in u.match_list:
            matches[u.id].add(id)
    
    return matches

def mtm_da_between_groups(proposer, propose_ids, receiver, receive_ids, target_min, matches, all_users_ids):
    propose = copy.deepcopy(proposer)
    receive = copy.deepcopy(receiver)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)

    #precompute whether each user is within propose and/or receive group
    prop_dict = {}
    rec_dict = {}
    for u_id in all_users_ids:
        prop_dict[u_id] = False
        rec_dict[u_id] = False
    for u_id in propose_ids:
        prop_dict[u_id] = True
    for u_id in receive_ids:
        rec_dict[u_id] = True

    # form initial preference lists
    for u in propose:
        u.temp_prefs = []
        for user_id in u.prefs:
            if rec_dict[user_id]:
                u.temp_prefs.append(user_id)
    
    for u in receive:
        u.temp_prefs = []
        u.temp_pref_ranks = {}
        rank = 1
        for user_id in u.prefs:
            if prop_dict[user_id]:
                u.temp_prefs.append(user_id)
                u.temp_pref_ranks[user_id] = rank
                rank += 1

    # consider relative sizes of propose & receive sides
    if len(receive_ids) > len(propose_ids):
        larger = receive
        smaller = propose
    else:
        larger = propose
        smaller = receive

    #assign quotas for each side
    for u in larger:
        u.quota = target_min
    
    quota = int(math.floor(target_min * len(larger) / len(smaller)))
    for u in smaller:
        u.quota = quota
        
    # randomly distribute the difference between the two sides
    difference = target_min * len(larger) - quota * len(smaller)
    for u in random.sample(smaller, difference):
        u.quota += 1
        
    while True:
        # proposal phase
        for u in propose:
            # propose until quota is reached
            while len(u.match_list) < u.quota and u.prop_pos < len(u.temp_prefs):
                receiver_id = u.temp_prefs[u.prop_pos]
                receiver = receive_dict[receiver_id]
                    
                u.match_list.append(receiver_id)
                u.prop_pos += 1
                
                u_rank = receiver.temp_pref_ranks[u.id]
                # insert in sorted order
                bisect.insort_left(receiver.match_list, (u_rank, u.id))
                
        # accept/reject phase
        for u in receive:
            # reject until match list size is within quota
            while len(u.match_list) > u.quota:
                # remove last element from match list
                rank, proposer_id = u.match_list.pop()
                proposer = propose_dict[proposer_id]
                
                # unmatch user
                proposer.match_list.remove(u.id)
                
        # check if finished
        finished = True
        for u in propose:
            if len(u.match_list) < u.quota and u.prop_pos < len(u.temp_prefs):
                finished = False
                break
                
        if finished:
            # end the algorithm
            break
                
    for u in propose:
        matches[u.id].update(u.match_list)
        
    for u in receive:
        for rank, id in u.match_list:
            matches[u.id].add(id)
    
    return matches

# return matches on all users
# just dummy code for now
def run_mtm_da_for_all():
    # users = user.gen_users(10)
    # users = user.add_prefs(users)
    users = user.load_users('anon_data_2016.txt')
    users = user.load_features(users, 'features_2016.txt')
    # users = user.calc_prefs(users)
    users = user.load_prefs(users, 'preferences_2016.txt')

    users_dict = user.map_users_list_to_dict(users)
    all_users_ids = users_dict.keys()

    #print "id: %d, prefs: %s" % (users[0].id, users[0].prefs[0:10])
    #for u in users[0].prefs[0:40]:
    #    print "id: %d, dist: %s" % (u, users[0].dist(users_dict[u]))

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

        matches[u.id] = set()
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

    '''
    print len(homo_m_id)
    print len(bi_m_id)
    print len(homo_f_id)
    print len(bi_m_id)
    print len(heter_m_id)
    print len(heter_f_id)
    '''

    #temporarily truncate for test reasons
    #heter_male = heter_male[:100]
    #heter_female = heter_female[:150]
    #heter_m_id = heter_m_id[:100]
    #heter_f_id = heter_f_id[:150]


    #call the iterated DA functions in 6 stages
    print "Computing matchings for homosexual & bisexual males..."
    matches = mtm_da_within_group((homo_male + bi_male), (homo_m_id + bi_m_id), int(overall_target_min * mixing_ratio), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual & bisexual females..."
    matches = mtm_da_within_group((homo_female + bi_female), (homo_f_id + bi_f_id), int(overall_target_min * mixing_ratio), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual males..."
    matches = mtm_da_within_group(homo_male, homo_m_id, int(overall_target_min * (1.0 - mixing_ratio)), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for homosexual females..."
    matches = mtm_da_within_group(homo_female, homo_f_id, int(overall_target_min * (1.0 - mixing_ratio)), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for bisexual & heterosexual males & females..."
    matches = mtm_da_between_groups((heter_male + bi_male), (heter_m_id + bi_m_id), (heter_female + bi_female), (heter_f_id + bi_f_id), int(overall_target_min * (1.0 - mixing_ratio)), matches, all_users_ids)
    # matches = mtm_da_between_groups((heter_female + bi_female), (heter_f_id + bi_f_id), (heter_male + bi_male), (heter_m_id + bi_m_id), int(overall_target_min * (1.0 - mixing_ratio)), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)
    print "Computing matchings for heterosexual males & females..."
    matches = mtm_da_between_groups(heter_male, heter_m_id, heter_female, heter_f_id, int(overall_target_min * mixing_ratio), matches, all_users_ids)
    # matches = mtm_da_between_groups(heter_female, heter_f_id, heter_male, heter_m_id, int(overall_target_min * mixing_ratio), matches, all_users_ids)
    user.analyze_num_matches(matches, users_dict)

    #create ranked list for each person by sorting their matches
    user.sort_all_match_lists(matches, users_dict)

    #check on how many matches people actually have
    user.analyze_num_matches(matches, users_dict)
    
    compatible_sizes = [
        [
            len(homo_male) + len(bi_male),
            len(heter_female) + len(bi_female),
            len(homo_male) + len(heter_female) + len(bi_male) + len(bi_female)
        ],
        [
            len(homo_female) + len(bi_female),
            len(heter_male) + len(bi_male),
            len(homo_female) + len(heter_male) + len(bi_male) + len(bi_female)
        ]
    ]

    for i in range(1, 4, 1):
        print '#####################################'
        print 'TOP %s MATCHES' % i
        print '#####################################'
        #check the utility values from rank perspective and distance perspective -- in two separate functions
        user.analyze_rank_utility(matches, users_dict, compatible_sizes, i)
        user.analyze_distance_utility(matches, users_dict, i)

run_mtm_da_for_all()
