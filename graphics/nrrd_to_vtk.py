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
    # print("image_array", np.min(image_array), np.max(image_array), np.unique(image_array, return_counts=True))

    objects_array = (image_array >= min) & (image_array <= max)
    # print("objects_array", np.min(objects_array), np.max(objects_array), np.unique(objects_array, return_counts=True))
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

def build_actor(image, color=(241/255, 214/255, 145/255), min:float=1, max:float=5000, opacity=0.15):
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
    # roi_actor1 = build_actor(roi, (1, 0, 0), 0.2, 1, 0.25)
    roi_actor2 = build_actor(roi, (1, 1, 0), 1.4, 2, 0.5)
    roi_actor3 = build_actor(roi, (1, 0, 1), 2.6, 3, 0.75)
    roi_actor4 = build_actor(roi, (1, 1, 1), 3.8, 5, 1)


    # Set up the rendering window, renderer, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # Add the actor to the scene
    # renderer.AddActor(brain_actor)
    # renderer.AddActor(roi_actor1)
    # renderer.AddActor(roi_actor2)
    # renderer.AddActor(roi_actor3)
    renderer.AddActor(roi_actor4)

    # renderer.SetBackground(0.1, 0.2, 0.4)  # background color (dark blue)
    renderer.SetBackground(0, 0, 0)  # background color (black)

    # Start the rendering loop
    render_window.Render()
    render_window_interactor.Start()


def visualize_brain_three_view(brain, roi):
    brain_actor = build_actor(brain, min=100, max=8000, opacity=0.2)
    roi_actor1 = build_actor(roi, (0.5, 0, 0), 1, 1, 1)
    roi_actor2 = build_actor(roi, (0.7, 0, 0), 2, 2, 0.2)
    roi_actor3 = build_actor(roi, (1, 0, 0), 3, 3, 0.15)
    roi_actor4 = build_actor(roi, (1, 0, 0), 4, 4, 0.5)

    # Create renderers for axial, coronal, sagittal
    renderer_axial = vtk.vtkRenderer()
    renderer_coronal = vtk.vtkRenderer()
    renderer_sagittal = vtk.vtkRenderer()

    for r in (renderer_axial, renderer_coronal, renderer_sagittal):
        r.AddActor(brain_actor)
        r.AddActor(roi_actor1)
        r.AddActor(roi_actor2)
        r.AddActor(roi_actor3)
        r.AddActor(roi_actor4)
        r.SetBackground(0.1, 0.1, 0.1)

    # Set up camera positions
    bounds = brain_actor.GetBounds()
    center = [(bounds[0] + bounds[1]) / 2.0,
              (bounds[2] + bounds[3]) / 2.0,
              (bounds[4] + bounds[5]) / 2.0]

    # Axial view (top down)
    cam_axial = renderer_axial.GetActiveCamera()
    cam_axial.SetFocalPoint(center)
    cam_axial.SetPosition(center[0], center[1], center[2] + 500)
    cam_axial.SetViewUp(0, 1, 0)

    # Coronal view (front)
    cam_coronal = renderer_coronal.GetActiveCamera()
    cam_coronal.SetFocalPoint(center)
    cam_coronal.SetPosition(center[0], center[1] - 500, center[2])
    cam_coronal.SetViewUp(0, 0, 1)

    # Sagittal view (side)
    cam_sagittal = renderer_sagittal.GetActiveCamera()
    cam_sagittal.SetFocalPoint(center)
    cam_sagittal.SetPosition(center[0] - 500, center[1], center[2])
    cam_sagittal.SetViewUp(0, 0, 1)

    # Create render window and interactor
    render_window = vtk.vtkRenderWindow()
    render_window.SetSize(900, 300)

    # Divide window into 3 viewports
    renderer_axial.SetViewport(0.0, 0.0, 0.33, 1.0)
    renderer_coronal.SetViewport(0.33, 0.0, 0.66, 1.0)
    renderer_sagittal.SetViewport(0.66, 0.0, 1.0, 1.0)

    render_window.AddRenderer(renderer_axial)
    render_window.AddRenderer(renderer_coronal)
    render_window.AddRenderer(renderer_sagittal)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    render_window.Render()
    interactor.Start()


def jpg_brain_three_view(brain, roi, jpg_path):
    brain_actor = build_actor(brain, min=100, max=8000, opacity=0.2)
    roi_actor1 = build_actor(roi, (1, 0, 0), 0.2, 1, 0.25)
    roi_actor2 = build_actor(roi, (1, 0, 0), 1.4, 2, 0.5)
    roi_actor3 = build_actor(roi, (1, 0, 0), 2.6, 3, 0.75)
    roi_actor4 = build_actor(roi, (1, 0, 0), 3.8, 5, 1)

    # Create renderers for axial, coronal, sagittal
    renderer_axial = vtk.vtkRenderer()
    renderer_coronal = vtk.vtkRenderer()
    renderer_sagittal = vtk.vtkRenderer()

    for r in (renderer_axial, renderer_coronal, renderer_sagittal):
        r.AddActor(brain_actor)
        r.AddActor(roi_actor1)
        r.AddActor(roi_actor2)
        r.AddActor(roi_actor3)
        r.AddActor(roi_actor4)
        r.SetBackground(0.1, 0.1, 0.1)

    # Set up camera positions
    bounds = brain_actor.GetBounds()
    center = [(bounds[0] + bounds[1]) / 2.0,
              (bounds[2] + bounds[3]) / 2.0,
              (bounds[4] + bounds[5]) / 2.0]

    # Axial view (top down)
    cam_axial = renderer_axial.GetActiveCamera()
    cam_axial.SetFocalPoint(center)
    cam_axial.SetPosition(center[0], center[1], center[2] + 500)
    cam_axial.SetViewUp(0, 1, 0)

    # Coronal view (front)
    cam_coronal = renderer_coronal.GetActiveCamera()
    cam_coronal.SetFocalPoint(center)
    cam_coronal.SetPosition(center[0], center[1] - 500, center[2])
    cam_coronal.SetViewUp(0, 0, 1)

    # Sagittal view (side)
    cam_sagittal = renderer_sagittal.GetActiveCamera()
    cam_sagittal.SetFocalPoint(center)
    cam_sagittal.SetPosition(center[0] - 500, center[1], center[2])
    cam_sagittal.SetViewUp(0, 0, 1)

    # Create render window and interactor
    render_window = vtk.vtkRenderWindow()
    render_window.SetSize(900, 300)

    # Divide window into 3 viewports
    renderer_axial.SetViewport(0.0, 0.0, 0.33, 1.0)
    renderer_coronal.SetViewport(0.33, 0.0, 0.66, 1.0)
    renderer_sagittal.SetViewport(0.66, 0.0, 1.0, 1.0)

    render_window.AddRenderer(renderer_axial)
    render_window.AddRenderer(renderer_coronal)
    render_window.AddRenderer(renderer_sagittal)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    render_window.Render()
    # Capture the image
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(render_window)
    windowToImageFilter.Update()

    # Save as JPEG
    jpg_writer = vtk.vtkJPEGWriter()
    jpg_writer.SetFileName(jpg_path)
    jpg_writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    jpg_writer.Write()

    # Save as pdf
    pdfExporter = vtk.vtkGL2PSExporter()
    pdfExporter.SetRenderWindow(render_window)
    pdfExporter.SetFileFormatToPDF()  # save as pdf
    pdfExporter.SetFilePrefix(jpg_path.replace(".jpg", ".pdf"))
    pdfExporter.Write()


if __name__ == "__main__":
    # Specify the path to your medical image
    # file_path = "z:/files/ctData.nrrd"
    # brain_path = "z:/files/RAD-AI-CNS-TUMOR-0149_T1_reg_SkullS_BiasC.nii.gz"
    # roi_path = "z:/files/RAD-AI-CNS-TUMOR-0149_tumor_seg_swinUNETR.nii.gz"

    brain_path  = 'Z:/scratch/rrs_radsurv_processor_1754428752.901332/preprocessed/RAD-AI-CNS-TUMOR-0310/Baseline/RAD-AI-CNS-TUMOR-0310_T1c_SRI24_SkullS_BiasC_IntStnd.nii.gz'
    roi_path = 'Z:/scratch/rrs_radsurv_processor_1754428752.901332/preprocessed/RAD-AI-CNS-TUMOR-0310/Baseline/tumor_seg_swinUNETR.nii.gz'

    brain = sitk.ReadImage(brain_path)
    roi = sitk.ReadImage(roi_path)

    visualize_brain_three_view(brain, roi)
    # jpg_brain_three_view(brain, roi, 'z:/scratch/jpg_test.jpg')
