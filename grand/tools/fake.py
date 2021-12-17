'''
fake module for workshop GRAND 2021
'''

import numpy as np


def max_2_vectors(v_a, v_b):
    '''
    return max of same index
    .. example::
       a=[1,5,6]
       b=[2,2,9]
       
       return=[2,5,9]
    :param v_a: numpy vector size n
    :param v_b: numpay vector size n
    :return: numpay vector size n
    '''
    v_ab= np.vstack((v_a,vb))
    return v_ab.max(axis=1)


def min_2_vectors(v_a, v_b):
    '''
    return min of same index
    .. example::
       a=[1,5,6]
       b=[2,2,9]
       
       return=[1,2,6]
       
    :param v_a: numpy vector size n
    :param v_b: numpay vector size n
    :return: numpay vector size n
    '''
    v_ab= np.vstack((v_a,v_a))
    ret = v_ab.min(axis=1)
    
    
def min_2_vectors_pos(v_a, v_b):
    '''
    return min of same index value vector and 0 if negative
    '''
    v_min = min_2_vectors(v_a, v_b)
    idx_neg     = np.where(v_min < 0)[0]
    v_min[idx_neg] = 0.0    
    return v_a
    