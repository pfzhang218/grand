from grand.tools.fake import *

v_a = np.array([1,5,6])
v_b = np.array([2,2,9])


def test_max_2_vectors():
    ret = max_2_vectors(v_a, v_b)
    ret_ok = np.array([2,5,9])
    np.testing.assert_array_equal(ret, ret_ok)
    



def test_min_2_vectors():
    ret = min_2_vectors(v_a, v_b)
    ret_ok = np.array([1,2,6])
    print(ret)
    np.testing.assert_array_equal(ret, ret_ok)


def test_min_2_vectors_pos():
    ret = min_2_vectors(v_a, v_b)
    ret_ok = np.array([1,2,6])
    print(ret)
    np.testing.assert_array_equal(ret, ret_ok)
    