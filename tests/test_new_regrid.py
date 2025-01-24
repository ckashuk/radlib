import unittest
import numpy as np

import regrid_3d

class TestNewRegrid(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_volume1d_value(self):
        volume1d = np.array([10, 11, 12, 13, 14, 15, 14, 13, 12, 11])
        volume1d_points = np.array([[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]])
        volume1d_points_outside = np.array([[-10], [-1], [10], [11], [100]])

        # real indices
        for volume_point in volume1d_points:
            value = regrid_3d.volume_value(volume1d, volume_point)
            self.assertEqual(value, volume1d[volume_point], f"error: volume_value wrong value for {volume_point}")

        # outside indices outside_value 0
        for volume_point in volume1d_points_outside:
            value = regrid_3d.volume_value(volume1d, volume_point)
            self.assertEqual(value, 0, f"error: volume_value outside_value=0 wrong value for {volume_point}")

        # outside indices outside_value 10
        for volume_point in volume1d_points_outside:
            value = regrid_3d.volume_value(volume1d, volume_point, outside_value=10)
            self.assertEqual(value, 10, f"error: volume_value outside_value=10 wrong value for {volume_point}")

        # outside indices outside_value min
        for volume_point in volume1d_points_outside:
            value = regrid_3d.volume_value(volume1d, volume_point, use_minimum=True)
            self.assertEqual(value, np.min(volume1d), f"error: volume_value outside_value=min wrong value for {volume_point}")

    def test_volume2d_value(self):
        volume2d = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
        volume2d_points = np.array([[0, 0], [0, 1], [0, 2],
                                    [1, 0], [1, 1], [1, 2],
                                    [2, 0], [2, 1], [2, 2]
                                    ])
        volume2d_points_outside = np.array([[-10, -10], [-1, -1], [-1, 1], [1, -1], [2, 3], [3, 2], [3, 3], [10, 10]])

        # real indices
        for volume_point in volume2d_points:
            value = regrid_3d.volume_value(volume2d, volume_point)
            self.assertEqual(value, regrid_3d.volume_value(volume2d, volume_point), f"error: volume_value wrong value for {volume_point}")

        # outside indices outside_value 0
        for volume_point in volume2d_points_outside:
            value = regrid_3d.volume_value(volume2d, volume_point)
            self.assertEqual(value, 0, f"error: volume_value outside_value=0 wrong value for {volume_point}")

        # outside indices outside_value 10
        for volume_point in volume2d_points_outside:
            value = regrid_3d.volume_value(volume2d, volume_point, outside_value=10)
            self.assertEqual(value, 10, f"error: volume_value outside_value=10 wrong value for {volume_point}")

        # outside indices outside_value min
        for volume_point in volume2d_points_outside:
            value = regrid_3d.volume_value(volume2d, volume_point, use_minimum=True)
            self.assertEqual(value, np.min(volume2d), f"error: volume_value outside_value=min wrong value for {volume_point}")


    def test_volume3d_value(self):
        volume3d = np.array([[[1, 1, 1], [1, 1, 1], [1, 1, 1]],
                              [[2, 2, 2], [2, 2, 2], [2, 2, 2]],
                              [[3, 3, 3], [3, 3, 3], [3, 3, 3]]])
        volume3d_points = np.array([
            [[[0, 0, 0], [0, 0, 1], [0, 0, 2]],
            [[0, 1, 0], [0, 1, 1], [0, 1, 2]],
            [[0, 2, 0], [0, 2, 1], [0, 2, 2]]],
            [[[0, 0, 0], [0, 0, 1], [0, 0, 2]],
            [[0, 1, 0], [0, 1, 1], [0, 1, 2]],
            [[0, 2, 0], [0, 2, 1], [0, 2, 2]]],
            [[[0, 0, 0], [0, 0, 1], [0, 0, 2]],
            [[0, 1, 0], [0, 1, 1], [0, 1, 2]],
            [[0, 2, 0], [0, 2, 1], [0, 2, 2]]]
        ])
        volume3d_points_outside = np.array([[-10, -10, -10], [-1, -1, -1], [-1, 1, 1], [1, -1, 1], [1, 1, -1], [2, 3, 3], [3, 2, 2], [3, 3, 3], [10, 10, 10]])

        # real indices
        for volume_point in volume3d_points.reshape(27, 3):
            value = regrid_3d.volume_value(volume3d, volume_point)
            self.assertEqual(value, regrid_3d.volume_value(volume3d,volume_point), f"error: volume_value wrong value for {volume_point}")

        # outside indices outside_value 0
        for volume_point in volume3d_points_outside:
            value = regrid_3d.volume_value(volume3d, volume_point)
            self.assertEqual(value, 0, f"error: volume_value outside_value=0 wrong value for {volume_point}")

        # outside indices outside_value 10
        for volume_point in volume3d_points_outside:
            value = regrid_3d.volume_value(volume3d, volume_point, outside_value=10)
            self.assertEqual(value, 10, f"error: volume_value outside_value=10 wrong value for {volume_point}")

        # outside indices outside_value min
        for volume_point in volume3d_points_outside:
            value = regrid_3d.volume_value(volume3d, volume_point, use_minimum=True)
            self.assertEqual(value, np.min(volume3d), f"error: volume_value outside_value=min wrong value for {volume_point}")

    def test_distance_from(self):
        for xyz in [1, 10, 20, 40, 80, 100]:
            point1 = np.array([xyz, xyz, xyz])
            point2 = np.array([xyz+1, xyz+1, xyz+1])
            dist = regrid_3d.distance_from(point1, point2)

            self.assertEqual(dist, np.sqrt(3), f'test_distance_from failed for x={xyz}')

    def test_simple_grid_resample_3d(self):
        points_volume = np.array([
            [[[0, 0, 0],
              [0, 0, 10]],
             [[0, 10, 0],
              [0, 10, 10]]],
            [[[10, 0, 0],
              [10, 0, 10]],
             [[10, 10, 0],
              [10, 10, 10]]]
        ])
        volume = np.array([[[10, 10], [10, 10]], [[20, 20], [20, 20]]])
        points_new = np.array([[[[3, 3, 3], [4.9999, 4.9999, 4.9999], [5.0001, 5.0001, 5.0001], [8, 8, 8]]]])

        new_volume_values = regrid_3d.grid_resample_3d_new(points_volume, volume, points_new, mode='linear')

        self.assertAlmostEqual(new_volume_values[:, :, 0][0][0], 13, 4, "grid_resample_3d failed")
        self.assertAlmostEqual(new_volume_values[:, :, 1][0][0], 14.9999, 4, "grid_resample_3d failed")
        self.assertAlmostEqual(new_volume_values[:, :, 2][0][0], 15.0001, 4, "grid_resample_3d failed")
        self.assertAlmostEqual(new_volume_values[:, :, 3][0][0], 18, 4, "grid_resample_3d failed")



if __name__ == "__main__":
    unittest.main()
