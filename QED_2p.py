import primaries_2p as pr
import numpy as np
import pickle
from tqdm import trange
from scipy.special import factorial
from scipy.integrate import dblquad


def mass_term(O1, O2):
    r = sum(sum( O1[m1]*O2[m2].conjugate() * 1j**(m1.conf_dim()-m2.conf_dim()) * (
        1/factorial(m1.conf_dim()+m2.conf_dim()-2)) * (

        factorial(m1.k1+m2.k1-1)*factorial(m1.k2+m2.k2) +\
            factorial(m1.k1+m2.k1)*factorial(m1.k2+m2.k2-1)

    ) for m1 in O1.monomials ) for m2 in O2.monomials )
    return r


def interaction_s_chan(O1, O2):
    r = sum(sum( O1[m1]*O2[m2].conjugate() * 1j**(m1.conf_dim()-m2.conf_dim()) * (
        1/(factorial(m1.k1+m1.k2+1)*factorial(m2.k1+m2.k2+1))) * (

        factorial(m1.k1)*factorial(m1.k2) *\
            factorial(m2.k1)*factorial(m2.k2)

    ) for m1 in O1.monomials ) for m2 in O2.monomials )
    return r


def interaction_t_chan(O1, O2):
    r = sum(sum( O1[m1]*O2[m2].conjugate() * 1j**(m1.conf_dim()-m2.conf_dim()) * (
        
        gross_integral(m1.k1,m1.k2,m2.k1,m2.k2)

    ) for m1 in O1.monomials ) for m2 in O2.monomials )
    return r


def gross_integral(*k):
    e = 0.01

    def egregious_integrand(x,y):
        return x**k[0] * (1-x)**k[1] * (
            y**k[2] * (1-y)**k[3] - x**k[2] * (1-x)**k[3] )/(x-y)**2

    r = dblquad(egregious_integrand, 0, 1, lambda x: 0, lambda x: x-e)[0]
    r += dblquad(egregious_integrand, 0, 1, lambda x: x+e, lambda x: 1)[0]
    return r


def interaction_term(O1, O2):
    return interaction_s_chan(O1, O2) - 0.5*interaction_t_chan(O1, O2)


def generate(del_max):
    """
    Generate a primary basis and mass matrix elements.
    Write everything to a json file called "2DQED_trunc_D{del_max}.json"
    The json file contains a dictionary:
    d["basis"] = the raw primary basis (load with 'load_raw' method)
    d["mass"] = the mass term in M^2
    d["inter"] = the interaction term in M^2
    """
    print('Generating primary basis...')
    B = pr.DirichletBasis()
    B.generate(del_max)

    print('Generating mass term matrix elements...')
    N = len(B.states)
    M = np.empty((N,N), dtype=complex)
    symmetric_index = (i for i in range(N**2) if i%N <= i//N)
    for i in trange(N*(N+1)//2):
        i = next(symmetric_index)
        j = i % N
        i //= N
        M[i,j] = M[j,i] = mass_term(B[i], B[j])
        M[j,i] = M[i,j].conjugate()

    print('Generating interaction matrix elements...')
    V = np.empty((N,N), dtype=complex)
    symmetric_index = (i for i in range(N**2) if i%N <= i//N)
    for i in trange(N*(N+1)//2):
        i = next(symmetric_index)
        j = i % N
        i //= N
        V[i,j] = interaction_term(B[i], B[j])
        V[j,i] = V[i,j].conjugate()

    print(f"Writing to file '2DQED_trunc_D{del_max}.json'...")
    d = {
        'basis': B.dump_raw(),
        'mass': [[M[i,j] for i in range(N)] for j in range(N)],
        'inter': [[V[i,j] for i in range(N)] for j in range(N)]
    }
    with open(f'2DQED_trunc_D{del_max}.bin', 'wb') as f:
        pickle.dump(d,f)

