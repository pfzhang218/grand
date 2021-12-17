from grand.tools.fake import *

v_a = np.array([1,5,6])
v_b = np.array([2,2,9])
v_c = np.array([-1,4,9])


def test_max_2_vectors():
    ret = max_2_vectors(v_a, v_b)
    ret_ok = np.array([2,5,9])
    np.testing.assert_array_equal(ret, ret_ok)


def test_min_2_vectors():
    ret = min_2_vectors(v_a, v_b)
    ret_ok = np.array([1,2,6])
    np.testing.assert_array_equal(ret, ret_ok)


def test_min_2_vectors_pos():
    ret_ok=[0,4,6]
    ret = min_2_vectors_pos(v_a,v_c)
    np.testing.assert_array_equal(ret, ret_ok)

