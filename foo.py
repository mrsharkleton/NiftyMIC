#!/usr/bin/python

## \file 
#
#  \author Michael Ebner (michael.ebner.14@ucl.ac.uk)
#  \date Aug 2016

## Import libraries 
import SimpleITK as sitk
import itk
import numpy as np
import sys

## Add directories to import modules
dir_src_root = "src/py/"
sys.path.append(dir_src_root)
# sys.path.append(dir_src_root + "reconstruction/regularization_parameter_estimator/")

## Import modules
import utilities.SimpleITKHelper as sitkh
import base.Stack as st
import base.Slice as sl
import utilities.StackManager as sm
import reconstruction.ScatteredDataApproximation as sda

import reconstruction.solver.TikhonovSolver as tk
import simulation.SimulatorSliceAcqusition as sa
import registration.Registration as myreg
import registration.StackInPlaneAlignment as sipa
import preprocessing.DataPreprocessing as dp
import preprocessing.BrainStripping as bs
import utilities.IntensityCorrection as ic
import registration.RegistrationSimpleITK as regsitk

import utilities.ScanExtractor as se
import utilities.FilenameParser as fp


## Pixel type of used 3D ITK image
PIXEL_TYPE = itk.D

## ITK image type
IMAGE_TYPE_2D = itk.Image[PIXEL_TYPE, 2]
IMAGE_TYPE_3D = itk.Image[PIXEL_TYPE, 3]
IMAGE_TYPE_3D_CV18 = itk.Image.CVD183
IMAGE_TYPE_3D_CV3 = itk.Image.CVD33


def append_reference_voxels_on_top(stack_to_copy, reference_image):
    stack = st.Stack.from_stack(stack_to_copy)

    stack_extended = stack.get_increased_stack(5)

    reference_image_resampled_sitk = sitk.Resample(reference_image.sitk, stack_extended.sitk, sitk.Euler3DTransform(), sitk.sitkNearestNeighbor)

    # sitk.Show(reference_image_resampled_sitk)
    nda_stack = sitk.GetArrayFromImage(stack_extended.sitk)
    nda_ref = sitk.GetArrayFromImage(reference_image_resampled_sitk)

    size = np.array(stack.sitk.GetSize())
    size_extended = np.array(stack_extended.sitk.GetSize())

    for k in range(size[2], size_extended[2]):
        nda_stack[k,:,:] = nda_ref[k,:,:]

    stack_extended_filled_sitk = sitk.GetImageFromArray(nda_stack)
    stack_extended_filled_sitk.CopyInformation(stack_extended.sitk)

    return st.Stack.from_sitk_image(stack_extended_filled_sitk, name=stack_to_copy.get_filename()+"_appended")

"""
Main Function
"""
if __name__ == '__main__':

    np.set_printoptions(precision=3)

    # dir_input = "data/test/"
    # filename_2D = "2D_BrainWeb"
    # filename_HRVolume = "FetalBrain_reconstruction_4stacks"
    # filename_stack = "fetal_brain_0"
    # filename_slice = "FetalBrain_stack1_registered_midslice"

    # dir_input = "test/data/"
    # filename_HRVolume = "recon_fetal_neck_mass_brain_cycles0_SRR_TK0_itermax20_alpha0.1"
    # filename_stack = "stack1_rotated_angle_z_is_pi_over_10"

    # HR_volume = st.Stack.from_filename(dir_input, filename_HRVolume)
    # stack = st.Stack.from_filename(dir_input, filename_stack, suffix_mask="_mask")

    # registration = myreg.Registration(fixed, moving)
    # registration.use_verbose(True)
    # registration.run_registration()

    # print registration.get_parameters()
    # transform_sitk = registration.get_registration_transform_sitk()

    # moving_resampled_sitk = sitk.Resample(moving.sitk, fixed.sitk, sitk.Euler3DTransform(), sitk.sitkBSpline)
    # moving_registered_sitk = sitk.Resample(moving.sitk, fixed.sitk, transform_sitk, sitk.sitkBSpline)

    # # sitkh.show_sitk_image([fixed.sitk, moving_resampled_sitk, moving_registered_sitk], ["fixed", "moving_orig", "moving_registered"])

    # sitkh.show_sitk_image(fixed.sitk,"fixed")
    # sitkh.show_sitk_image(moving_resampled_sitk,"moving_resampled")
    # sitkh.show_sitk_image(moving_registered_sitk,"moving_registered")

    # # image_2D_itk = sitkh.read_itk_image(dir_input + filename_2D + ".nii.gz", dim=2, pixel_type=PIXEL_TYPE)
    # # HRvolume_itk = sitkh.read_itk_image(dir_input + filename_HRVolume + ".nii.gz", dim=3, pixel_type=PIXEL_TYPE)
    # # slice_itk = sitkh.read_itk_image(dir_input + filename_slice + ".nii.gz", dim=3, pixel_type=PIXEL_TYPE)
    # # slice_itk = HRvolume_itk

    # image_2D_sitk = sitk.ReadImage(dir_input + filename_2D + ".nii.gz")

    # DIR_INPUT = "data/placenta/";                   filename_stack = "a23_05"
    # # DIR_INPUT = "data/fetal_neck_mass_brain/";      filename_stack = "0"
    # stack = st.Stack.from_filename(DIR_INPUT, filename_stack, suffix_mask="_mask")

    # data_preprocessing = dp.DataPreprocessing.from_stacks([stack])
    # # data_preprocessing.set_dilation_radius(0)
    # data_preprocessing.run_preprocessing()
    # stack = data_preprocessing.get_preprocessed_stacks()[0]

    # inplane_reg = sipa.StackInPlaneAlignment()
    # inplane_reg.set_stack(stack)

    # inplane_reg.run_registration()

    # stack_inplane_reg = inplane_reg.get_stack()

    # # stack_inplane_reg.get_resampled_stack_from_slices().show(1)
    # stack_registered_sitk = stack_inplane_reg.get_resampled_stack_from_slices(interpolator="Linear").sitk
    # sitkh.show_sitk_image([stack.sitk, stack_registered_sitk], ["original", "inplane-registered"])

    subject = "2"
    filename = "002-30yr-AxT2"
    DIR_ROOT_DIRECTORY = "/Users/mebner/UCL/Data/30_year_old_data/"
    dir_input_data = DIR_ROOT_DIRECTORY + "Subject_" + subject + "/"

    dir_input = "studies/30YearMSData/Subject" + subject + "/data_preprocessing/"
    filename = "Baseline_1_downsampled_roughly_scaled"
    # filename = "Baseline_5_inplane_aligned_with_reference"
    # filename = "Baseline_L-BFGS-B_alpha0_itermax5"
    filename_ref = "002-30yr-AxT2"
    filename_ref = "002-10yr-PD:T2"
    
    # reference_image = st.Stack.from_filename(dir_input, filename, "_mask")
    # brain_stripping = bs.BrainStripping.from_filename(dir_input, filename)
    # brain_stripping = bs.BrainStripping.from_sitk_image(reference_image.sitk)
    # brain_stripping = bs.BrainStripping()
    # brain_stripping.set_input_image_sitk(reference_image.sitk)
    # brain_stripping.compute_brain_mask(1)
    # brain_stripping.compute_brain_image(0)
    # brain_stripping.compute_skull_image(0)
    # brain_stripping.set_bet_options("-f 0.3")

    # brain_stripping.run_stripping()
    # original_sitk = brain_stripping.get_input_image_sitk()
    # brain_mask_sitk = brain_stripping.get_brain_mask_sitk()
    # brain_sitk = brain_stripping.get_brain_image_sitk()
    # skull_mask_sitk = brain_stripping.get_skull_image_sitk()

    # sitkh.show_sitk_image([original_sitk], segmentation=brain_mask_sitk)
    # sitkh.show_sitk_image([original_sitk, brain_sitk], segmentation=skull_mask_sitk)

    # if 0:
    #     if filename_ref in ["002-10yr-PD:T2"]:
    #         reference_image_sitk = sitkh.read_sitk_vector_image(dir_input_data + filename_ref + ".nii", return_vector_index=0)
    #         reference_image = st.Stack.from_sitk_image(reference_image_sitk, name=filename_ref[0:-3])
    #     else:
    #         reference_image = st.Stack.from_filename(dir_input_data, filename_ref)
    #     stack = st.Stack.from_filename(dir_input, filename)

    #     registration = regsitk.RegistrationSimpleITK(fixed=stack, moving=reference_image)
    #     registration.set_interpolator("Linear")
    #     registration.set_metric("Correlation")
    #     registration.set_centered_transform_initializer("GEOMETRY")
    #     registration.use_verbose(True)
    #     registration.run_registration()
    #     transformation_sitk = registration.get_registration_transform_sitk()

    #     reference_image_resampled_sitk = sitk.Resample(reference_image.sitk, stack.sitk, transformation_sitk)
    #     # sitkh.show_sitk_image([stack.sitk, reference_image_resampled_sitk])
    
    # # intensity_correction = ic.IntensityCorrection.from_sitk_image(image_sitk=stack.sitk)
    # intensity_correction = ic.IntensityCorrection.from_sitk_image(image_sitk=stack.sitk, reference_sitk=reference_image_resampled_sitk, percentile=10)
    # intensity_correction.run_intensity_correction()
    # foo_sitk = intensity_correction.get_intensity_corrected_sitk_image()

    # sitkh.show_sitk_image([stack.sitk, foo_sitk, reference_image_resampled_sitk], title=["original", "corrected", "reference"])
    # reference_image.show()


    ## Set offset for semi-automatic brain extraction to extract brain by click
    ## at left filled circle (Baseline and 1year) and corner L-shape (5year)
    selection_window_offset = {
        "Baseline"  : np.array([100,-900]),
        "1year"     : np.array([100,-900]),
        "5year"     : np.array([-1450,-550])   
    }

    ## Different type of MR film scan for 5 years requires a different frame
    ## size selection in order to fit the brain inside
    selection_window_dimension = {
        "Baseline"  : np.array([1350,1600]),
        "1year"     : np.array([1350,1600]),
        "5year"     : np.array([1100,1250])   
    }
    timepoint = "Baseline"

    filename_parser = fp.FilenameParser()
    filenames = filename_parser.get_filenames_which_match_pattern_in_directory(directory=dir_input_data, pattern=timepoint, filename_extension=".dcm")

    scan_extractor = se.ScanExtractor(dir_input=dir_input_data, filenames=filenames, number_of_mr_films=1, selection_window_offset=selection_window_offset[timepoint], selection_window_dimension=selection_window_dimension[timepoint], use_verbose=True, dir_output_verbose="/tmp/foo")

    scan_extractor.run_semiautomatic_image_extraction()

    image_sitk = scan_extractor.get_sitk_stack_of_extracted_scans()

