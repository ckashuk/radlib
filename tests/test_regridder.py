import unittest

import SimpleITK as sitk
import numpy as np

from radlib.dcm import generate_grid, evaluate_at_continuous_index_wrapper

"""
tests for image regridder functionality
"""
class TestRegridder(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self):
        pass


    def generate_image(self, volume, origin, spacing):
        image = sitk.GetImageFromArray(volume)
        image.SetOrigin(origin)
        image.SetSpacing(spacing)
        return image

    def generate_grid_test(self,
                           test_volume,
                           expected_grid,
                           test_origin=None,
                           test_spacing=None,
                           err_msg="test failed"):

        # function definition for reference:
        # def generate_grid(img: sitk.Image) -> np.ndarray:

        # simple 1-1 test
        if test_spacing is None:
            test_spacing = [1, 1, 1]
        if test_origin is None:
            test_origin = [0, 0, 0]

        image = self.generate_image(volume=test_volume,
                                    origin=test_origin,
                                    spacing=test_spacing)

        grid = generate_grid(image)
        np.testing.assert_allclose(grid, expected_grid, err_msg=err_msg)

    def test_generate_grid_simple(self):
        # function definition for reference:
        # def generate_grid(img: sitk.Image) -> np.ndarray:

        # simple 1-1 test
        self.generate_grid_test(test_volume=[[[1, 1], [1, 1]], [[2, 2], [2, 2]]],
                                test_origin=[0, 0, 0],
                                test_spacing=[1, 1, 1],
                                expected_grid = np.array([[[[0, 0, 0], [0, 0, 1]],
                                                           [[0, 1, 0], [0, 1, 1]]],
                                                          [[[1, 0, 0], [1, 0, 1]],
                                                           [[1, 1, 0], [1, 1, 1]]]]),
                                err_msg="generate_grid simple 1-1 test failed")


    def test_generate_grid_origin(self):
        # change origin
        self.generate_grid_test(test_volume=[[[1, 1], [1, 1]], [[2, 2], [2, 2]]],
                                test_origin=[10, 10, 10],
                                test_spacing=[1, 1, 1],
                                expected_grid = np.array([[[[10, 10, 10], [10, 10, 11]],
                                                           [[10, 11, 10], [10, 11, 11]]],
                                                          [[[11, 10, 10], [11, 10, 11]],
                                                           [[11, 11, 10], [11, 11, 11]]]]),
                                err_msg="generate_grid origin test failed")


    def test_generate_grid_spacing(self):
        # change spacing
        self.generate_grid_test(test_volume=[[[1, 1], [1, 1]], [[2, 2], [2, 2]]],
                                test_origin=[0, 0, 0],
                                test_spacing=[2, 2, 2],
                                expected_grid = np.array([[[[0, 0, 0], [0, 0, 2]],
                                                           [[0, 2, 0], [0, 2, 2]]],
                                                          [[[2, 0, 0], [2, 0, 2]],
                                                           [[2, 2, 0], [2, 2, 2]]]]),
                                err_msg="generate_grid spacing test failed")


    def test_generate_grid_origin_spacing(self):
        # change origin and spacing
        self.generate_grid_test(test_volume=[[[1, 1], [1, 1]], [[2, 2], [2, 2]]],
                                test_origin=[10, 10, 10],
                                test_spacing=[2, 2, 2],
                                expected_grid = np.array([[[[10, 10, 10], [10, 10, 12]],
                                                           [[10, 12, 10], [10, 12, 12]]],
                                                          [[[12, 10, 10], [12, 10, 12]],
                                                           [[12, 12, 10], [12, 12, 12]]]]),
                                err_msg="generate_grid origin/spacing test failed")


    def test_evaluate_at_continuous_grid_wrapper(self):
        # function definition for reference:
        # def evaluate_at_continuous_index_wrapper(img:sitk.Image,
        #                                          new_point: np.ndarray,
        #                                          default_value:float=0,
        #                                          mode=sitk.sitkLinear)-> Union[int, float]:

        # we can take advantage of using simpleitk and only test the wrapper, we don't need to unit test
        # EvaluateAtContinuousIndex!

        # simple image
        test_volume = [[[1, 1], [1, 1]], [[2, 2], [2, 2]]]
        test_origin = [10, 10, 10]
        test_spacing = [2, 2, 2]
        test_image = self.generate_image(volume=test_volume, origin=test_origin, spacing=test_spacing)

        # test evaluate at simple index
        value = evaluate_at_continuous_index_wrapper(test_image, np.array([0., 0., 0.]))
        self.assertEqual(value, 1, "evaluate_at_continuous_grid_wrapper simple test failed")

        # test evaluate at continuous index
        value = evaluate_at_continuous_index_wrapper(test_image, np.array([0.5, 0.5, 0.5]))
        self.assertEqual(value, 1.5, "evaluate_at_continuous_grid_wrapper continuous test failed")

        # test evaluate at negative index
        value = evaluate_at_continuous_index_wrapper(test_image, np.array([-1., -1., -1.]))
        self.assertEqual(value, 0, "evaluate_at_continuous_grid_wrapper negative index test failed")

        # test evaluate at overlow index
        value = evaluate_at_continuous_index_wrapper(test_image, np.array([10., 10., 10.]))
        self.assertEqual(value, 0, "evaluate_at_continuous_grid_wrapper overflow index test failed")

        # test default value
        value = evaluate_at_continuous_index_wrapper(test_image, np.array([10., 10., 10.]), default_value=100)
        self.assertEqual(value, 100, "evaluate_at_continuous_grid_wrapper default_value test failed")

    def test_evaluate_at_continuous_grid_wrapper_interpolation_mode(self):
        # simple image
        test_volume = [[[1, 1], [1, 1]], [[2, 2], [2, 2]]]
        test_origin = [10, 10, 10]
        test_spacing = [2, 2, 2]
        test_image = self.generate_image(volume=test_volume, origin=test_origin, spacing=test_spacing)

        # linear interpolation will give 1 + 10% = 1.1, nearest neighbor will give 1,
        # spline will give 1.0279999999999994, derived by experiment
        # TODO: csk 202501 can we do more here?
        value_default = evaluate_at_continuous_index_wrapper(test_image, np.array([0.1, 0.1, 0.1]))
        value_linear = evaluate_at_continuous_index_wrapper(test_image, np.array([0.1, 0.1, 0.1]), interp=sitk.sitkLinear)
        value_nearest = evaluate_at_continuous_index_wrapper(test_image, np.array([0.1, 0.1, 0.1]), interp=sitk.sitkNearestNeighbor)
        value_spline = evaluate_at_continuous_index_wrapper(test_image, np.array([0.1, 0.1, 0.1]), interp=sitk.sitkBSpline)

        self.assertEqual(value_default, 1.1, "evaluate_at_continuous_grid_wrapper default interpolation_mode failed")
        self.assertEqual(value_linear, 1.1, "evaluate_at_continuous_grid_wrapper linear interpolation_mode failed")
        self.assertEqual(value_nearest, 1.0, "evaluate_at_continuous_grid_wrapper nearest interpolation_mode failed")
        self.assertEqual(value_spline, 1.0279999999999994, "evaluate_at_continuous_grid_wrapper bspline interpolation_mode failed")




    def test_regridded_volume(self):
        # function definition for reference:
        # def generate_regridded_volume(img: sitk.Image,
        #                               grid: np.ndarray = None,
        #                               default_value: float = 0,
        #                               mode=sitk.sitkLinear) -> np.ndarray:

        #
        pass

    def test_regridded_image(self):
        # function definition for reference:
        # def generate_regridded_image(img: sitk.Image,
        #                              grid: np.ndarray = None,
        #                              mode=sitk.sitkLinear,
        #                              copy_tags=True) -> sitk.Image:

        pass


if __name__ == "__main__":
    unittest.main()
