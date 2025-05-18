import numpy as np

def test_numpy():
    # Create a 1D array
    arr_1d = np.array([1, 2, 3, 4, 5])
    assert arr_1d.shape == (5,)
    assert arr_1d[0] == 1
    assert arr_1d[4] == 5

    # Create a 2D array
    arr_2d = np.array([[1, 2, 3], [4, 5, 6]])
    assert arr_2d.shape == (2, 3)
    assert arr_2d[0, 0] == 1
    assert arr_2d[1, 2] == 6

    # Create a 3D array
    arr_3d = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
    assert arr_3d.shape == (2, 2, 2)
    assert arr_3d[0, 0, 0] == 1
    assert arr_3d[1, 1, 1] == 8
    
    print("All tests passed!")
    
if __name__ == "__main__":
    test_numpy()