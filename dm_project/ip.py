import cplex
import user
from user import User
import itertools

max_match = 15
min_match = 10
const_num_users = 1500
load_real_data = False

# useful for one of the constraints later on
def swap_match_name(s):
    mid = s.index('_')
    return s[mid+1:] + '_' + s[:mid]

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
user_dists = {}
for u1 in user_ids:
    match_names[u1] = [str(u1) + "_" + str(u2) for u2 in user_ids if
                        (u1 != u2 and users_dict[u1].is_compatibile(users_dict[u2]))]
    user_dists[u1] = [users_dict[u1].dist(users_dict[u2]) for u2 in user_ids if
                        (u1 != u2 and users_dict[u1].is_compatibile(users_dict[u2]))]
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
# min match constraints
prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = match_names[u],
                                                         val = [1.0] * len(match_names[u]))
                                        for u in user_ids],
                            senses = ['G'] * num_users,
                            rhs = [min_match - 1] * num_users,
                            names = ['min_' + str(u) for u in user_ids])
# max match constraints
prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = match_names[u],
                                                         val = [1.0] * len(match_names[u]))
                                        for u in user_ids],
                            senses = ['L'] * num_users,
                            rhs = [max_match + 1] * num_users,
                            names = ['max_' + str(u) for u in user_ids])
# bidirectional match constraints
# we repeat some (a_ij - a_ji = 0 <-> a_ji - a_ij = 0), but that's fine
for u in user_ids:
    prob.linear_constraints.add(lin_expr = [cplex.SparsePair(ind = [m, swap_match_name(m)],
                                                             val = [1.0, -1.0])
                                            for m in match_names[u]],
                                senses = ['E'] * len(match_names[u]),
                                rhs = [0] * len(match_names[u]),
                                names = ['equal_' + m for m in match_names[u]])

# save the problem for future use
if load_real_data:
    prob.write('2016_ip_problem.gz')

# Solve!
prob.solve()
print "Status: %s" % prob.solution.get_status_string()
print "Final objective value: %s" % prob.solution.get_objective_value()


# Save our solution
filename = 'ip_matches_%d_real_%s.txt' % (num_users, load_real_data)
f = open(filename, 'w')
for u in user_ids:
    f.write((str)(u))
    match_solutions = prob.solution.get_values(match_names[u])
    for i in xrange(len(match_names[u])):
        if (match_solutions[i] == 1.0):
            match_id = str(match_names[u][i])[str(match_names[u][i]).index('_') + 1:]
            f.write(':' + match_id + ',' + str(users_dict[u].dist(users_dict[int(match_id)])))
    f.write('\n')
f.close()
