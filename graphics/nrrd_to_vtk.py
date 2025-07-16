import SimpleITK as sitk
import vtk
import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk

from radlib.dcm.total_segmentator import get_segments_by_tag


# Step 1: Load the medical image (DICOM, NIfTI, or any format SimpleITK supports)
def load_medical_image(file_path):
    # For DICOM: sitk.ReadImage("path_to_dicom_folder")
    # For NIfTI: sitk.ReadImage("path_to_nifti_file")
    image = sitk.ReadImage(file_path)
    return image


# Step 2: Threshold the image to extract bone regions (CT scans typically have bone in the range 300-3000 HU)
def threshold_bones(image, lower_threshold=300, upper_threshold=3000):
    # Convert SimpleITK image to numpy array
    image_array = sitk.GetArrayFromImage(image)

    # Apply thresholding: Select the bone regions based on density
    bones = (image_array >= lower_threshold) & (image_array <= upper_threshold)

    # Convert the numpy array back to a SimpleITK image
    bones_image = sitk.GetImageFromArray(bones.astype(np.uint8))
    bones_image.CopyInformation(image)  # Copy metadata like spacing, origin
    return bones_image


# Step 3: Convert thresholded image to VTK PolyData (3D volume)
def image_to_vtk_polydata(image, min, max):
    # Convert SimpleITK image to numpy array
    image_array = sitk.GetArrayFromImage(image)

    objects_array = (image_array >= min) & (image_array <= max)

    # Get the dimensions of the image
    size = objects_array.shape
    spacing = image.GetSpacing()

    # Convert the numpy array to vtkImageData
    vtk_image = vtk.vtkImageData()
    vtk_image.SetDimensions(size[2], size[1], size[0])  # vtk uses Z, Y, X ordering
    vtk_image.SetSpacing(spacing)
    vtk_image.SetOrigin(image.GetOrigin())

    # Use vtkImageImport to load the image into VTK
    vtk_array = numpy_to_vtk(objects_array.ravel(), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
    vtk_image.GetPointData().SetScalars(vtk_array)

    # Step 4: Extract the bone surface using vtkMarchingCubes (iso-surface extraction)
    contour_filter = vtk.vtkMarchingCubes()
    contour_filter.SetInputData(vtk_image)
    contour_filter.ComputeNormalsOn()
    contour_filter.SetValue(0, 1)  # Extract the contour for voxel value 1 (bone)
    contour_filter.Update()

    # The output is a PolyData object
    poly_data = contour_filter.GetOutput()
    return poly_data

def build_actor(image, color=(241/255, 214/255, 145/255), min=1, max=5000, opacity=0.15):
    poly_data = image_to_vtk_polydata(image, min, max)

    # Create a VTK mapper to map the PolyData to graphics representation
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly_data)
    mapper.SetColorModeToDirectScalars()
    mapper.SetScalarModeToUseCellData()

    # Create an actor to represent the bone surface
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    # colors = get_segments_by_tag('bone')
    # print(colors['skull.nii.gz'])
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)

    return actor


# Step 5: Visualize the extracted 3D bone surface using VTK
def visualize_brain(brain, roi):
    brain_actor = build_actor(brain, min=100, max=8000, opacity=0.2)
    roi_actor = build_actor(roi, (1, 0, 0), 0.8, 1, 1)

    # Set up the rendering window, renderer, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # Add the actor to the scene
    renderer.AddActor(brain_actor)
    renderer.AddActor(roi_actor)

    # renderer.SetBackground(0.1, 0.2, 0.4)  # background color (dark blue)
    renderer.SetBackground(0, 0, 0)  # background color (black)

    # Start the rendering loop
    render_window.Render()
    render_window_interactor.Start()


if __name__ == "__main__":
    # Specify the path to your medical image
    # file_path = "z:/files/ctData.nrrd"
    brain_path = "z:/files/RAD-AI-CNS-TUMOR-0149_T1_reg_SkullS_BiasC.nii.gz"
    roi_path = "z:/files/RAD-AI-CNS-TUMOR-0149_tumor_seg_swinUNETR.nii.gz"

    brain = sitk.ReadImage(brain_path)
    roi = sitk.ReadImage(roi_path)
    print(np.min(sitk.GetArrayFromImage(roi)), np.max(sitk.GetArrayFromImage(roi)))
    visualize_brain(brain, roi)
