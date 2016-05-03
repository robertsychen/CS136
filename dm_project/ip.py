import cplex
import user
from user import User
import itertools

num_users = 500
max_match = 15
min_match = 10

# useful for one of the constraints later on
def swap_match_name(s):
    mid = s.index('_')
    return s[mid+1:] + '_' + s[:mid]

# random users...
users = user.gen_users(num_users)
users = user.calc_prefs(users, save=False)
users = user.filter_prefs(users)
# or actual users...?
# users = user.load_users('anon_data_2016.txt')
# users = user.load_features(users, 'features_2016.txt')
# users = user.load_prefs(users, 'preferences_2016.txt')
# users = user.filter_prefs(users)

users_dict = user.map_users_list_to_dict(users)
user_ids = [u.id for u in users]
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

# Solve!
prob.solve()
