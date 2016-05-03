import cplex
import user
from user import User
import itertools

max_match = 18
min_match = 9
const_num_users = 1500
load_real_data = True # use the actual DM data?

# useful for one of the constraints later on
def swap_match_name(s):
    mid = s.index('_')
    return s[mid+1:] + '_' + s[:mid]

def find_swap_index(names, name, indices):
    mid = name.index('_')
    u1 = (int)(name[:mid])
    u2 = (int)(name[mid+1:])
    swapped_name = swap_match_name(name)
    for i in xrange(len(names[u2])):
        if names[u2][i] == swapped_name:
            return indices[u2][i]

# random users...
if not load_real_data:
    users = user.gen_users(const_num_users)
    users = user.calc_prefs(users, save=True)
    users = user.filter_prefs(users)
# or actual users...?
else:
    users = user.load_users('anon_data_2016.txt')
    users = user.load_features(users, 'features_2016.txt')
    users = user.load_prefs(users, 'preferences_2016.txt')
    users = user.filter_prefs(users)

# userful variables
users_dict = user.map_users_list_to_dict(users)
user_ids = [u.id for u in users]
num_users = len(user_ids)
# all possible matches and distances
match_names = {}
match_indices = {}
user_dists = {}
running_num_users = 0
for u1 in user_ids:
    match_names[u1] = [str(u1) + "_" + str(u2) for u2 in user_ids if
                        (u1 != u2 and users_dict[u1].is_compatibile(users_dict[u2]))]
    match_indices[u1] = range(running_num_users, running_num_users + len(match_names[u1]))
    user_dists[u1] = [users_dict[u1].dist(users_dict[u2]) for u2 in user_ids if
                        (u1 != u2 and users_dict[u1].is_compatibile(users_dict[u2]))]
    running_num_users += len(match_names[u1])
# be careful that these correspond to each other...
flat_match_names = list(itertools.chain.from_iterable(match_names.values()))
flat_user_dists = list(itertools.chain.from_iterable(user_dists.values()))

# Set up the problem
prob = cplex.Cplex()
# objective: min sum [a_ij * d_ij], for all i,j in users
prob.objective.set_sense(prob.objective.sense.minimize)
# add variables for problem, as well as objective constraint coefficients
prob.variables.add(obj = flat_user_dists,
                   types = [prob.variables.type.binary] * len(flat_match_names),
                   names = flat_match_names)
print "Loaded variables!"
# min match constraints
prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = match_indices[u], # match_names[u],
                                                         val = [1.0] * len(match_names[u]))
                                        for u in user_ids],
                            senses = ['G'] * num_users,
                            rhs = [min_match - 1] * num_users)
print "Loaded mins!"
# max match constraints
prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = match_indices[u], # match_names[u],
                                                         val = [1.0] * len(match_names[u]))
                                        for u in user_ids],
                            senses = ['L'] * num_users,
                            rhs = [max_match + 1] * num_users)
print "Loaded maxs!"
# bidirectional match constraints
# we repeat some (a_ij - a_ji = 0 <-> a_ji - a_ij = 0), but that's fine
for u in user_ids:
    print '\rLoading equals for user %d' % u,
    prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = [m, find_swap_index(match_names, flat_match_names[m], match_indices)],
                                                             val = [1.0, -1.0])
                                            for m in match_indices[u]],
                                senses = ['E'] * len(match_names[u]),
                                rhs = [0] * len(match_names[u]))
print "Loaded equals!"

# save the problem for future use
if load_real_data:
    prob.write('2016_ip_problem.gz')

# Solve!
prob.solve()
print "Status: %s" % prob.solution.get_status_string()
print "Final objective value: %s" % prob.solution.get_objective_value()

# for later analysis of results
if not load_real_data:
    # Save the users
    filename = 'random_data_%d.txt' % (num_users)
    f = open(filename, 'w')
    for u in users:
        print '\rWriting data for user %d to file' % u.id,
        f.write((str)(u.id) + ':')
        f.write('foo:')
        f.write('foo:')
        if u.gender == 0:
            f.write('Male:')
        else:
            f.write('Female:')
        if u.seeking == 0:
            f.write('Men:')
        elif u.seeking == 1:
            f.write('Women:')
        else:
            f.write('Both:')
        f.write('bar')
        f.write('\n')
    f.close()
    print '(Data write complete!)'

    # Save the features
    filename = 'random_features_%d.txt' % (num_users)
    f = open(filename, 'w')
    for u in users:
        print '\rWriting features for user %d to file' % u.id,
        f.write((str)(u.id) + ':')
        f.write(':'.join(map(str,u.features)))
        f.write('\n')
    f.close()
    print '(Features write complete!)'

# Save our solution
filename = 'ip_matches_%d_real_%s.txt' % (num_users, load_real_data)
f = open(filename, 'w')
for u in user_ids:
    print '\rWriting matches for user %d to file' % u,
    f.write((str)(u))
    match_solutions = prob.solution.get_values(match_indices[u])
    for i in xrange(len(match_names[u])):
        if (match_solutions[i] == 1.0):
            match_id = str(match_names[u][i])[str(match_names[u][i]).index('_') + 1:]
            f.write(':' + match_id + ',' + str(users_dict[u].dist(users_dict[int(match_id)])))
    f.write('\n')
f.close()
print '(Matches write complete!)'
