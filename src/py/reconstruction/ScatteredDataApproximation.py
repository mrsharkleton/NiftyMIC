# \file ScatteredDataApproximation.py
#  \brief Implementation of two different approaches for Scattered Data
#         Approximation (SDA)
#
#  \author Michael Ebner (michael.ebner.14@ucl.ac.uk)
#  \date April 2016


# Import libraries
import os                       # used to execute terminal commands in python
import sys
import itk
import SimpleITK as sitk
import numpy as np
import time

# Import modules from src-folder
import base.Stack as st
import utilities.SimpleITKHelper as sitkh


# Class implementing Scattered Data Approximation
class ScatteredDataApproximation:

    ##
    # Constructor
    # \date          2017-07-12 15:48:33+0100
    #
    # \param         self         The object
    # \param         stacks       list of Stack objects containing all stacks
    #                             used for the reconstruction
    # \param[in,out] HR_volume    Stack object containing the current estimate
    #                             of the HR volume (required for defining HR
    #                             space)
    # \param         sigma        The sigma
    # \param         sigma_array  The sigma array
    # \post          HR_volume is updated with current volumetric estimate
    #
    def __init__(self, stacks, HR_volume, sigma=1, sigma_array=None):

        # Initialize variables
        self._stacks = stacks
        self._N_stacks = len(stacks)
        self._HR_volume = HR_volume

        # Define sigma for recursive smoothing filter
        if sigma_array is None:
            self._sigma_array = np.ones(3)*sigma
        elif len(sigma_array) is not 3:
            raise ValueError("Error: Sigma array must contain 3 elements")
        else:
            self._sigma_array = np.array(sigma_array)

        # Define dictionary to choose computational approach for SDA
        self._run_reconstruction = {
            "Shepard-YVV":   self._run_discrete_shepard_reconstruction,
            "Shepard-Deriche":   self._run_discrete_shepard_based_on_Deriche_reconstruction,
        }
        self._sda_approach = "Shepard-YVV"    # default approximation approach

    # Set sigma used for recursive Gaussian smoothing. Same sigma is used
    #  in each axis, i.e. isotropic smoothing is applied. Sigma is measured
    #  in the units of image spacing.
    #  \param[in] sigma, scalar
    def set_sigma(self, sigma):
        self._sigma_array = np.ones(3)*sigma

    # ## Get sigma used for recursive Gaussian smoothing.
    # #  \return sigma array, numpy array
    # def get_sigma(self):
    #     return self._sigma_array

    # Set array of standard deviations used for recursive Gaussian smoothing
    #  in each direction. Sigmas are measured in the units of image spacing.
    #  You may use the method SetSigma to set the same value across each axis or
    #  use the method SetSigmaArray if you need different values along each axis
    #  \param[in] sigma_array 3D array containing the standard deviation in each direction
    def set_sigma_array(self, sigma_array):
        if len(sigma_array) is not 3:
            raise ValueError("Error: Sigma array must contain 3 elements")

        self._sigma_array = np.array(sigma_array)

    # Get array of standard deviations used for recursive Gaussian smoothing
    #  in each direction. Sigmas are measured in the units of image spacing.
    #  \return sigma array, numpy array
    def get_sigma_array(self):
        return self._sigma_array

    # Set approach for approximating the HR volume. It can be either
    #  'Shepard-YVV' or 'Shepard-Deriche'
    #  \param[in] sda_approach either 'Shepard-YVV' or 'Shepard-Deriche', string
    def set_approach(self, sda_approach):
        if sda_approach not in ["Shepard-YVV", "Shepard-Deriche"]:
            raise ValueError(
                "Error: SDA approach can only be either 'Shepard-YVV' or 'Shepard-Deriche'")

        self._sda_approach = sda_approach

    # Get chosen type of regularization.
    #  \return regularization type as string
    def get_approach(self):
        return self._sda_approach

    # Get current estimate of HR volume
    #  \return current estimate of HR volume, instance of Stack
    def get_reconstruction(self):
        return self._HR_volume

    # Computed reconstructed volume based on current estimated positions of
    # slices
    def run_reconstruction(self):
        print("Chosen SDA approach: " + self._sda_approach)
        print("Smoothing parameter sigma = " + str(self._sigma_array))

        t0 = time.clock()

        self._run_reconstruction[self._sda_approach]()

        time_elapsed = time.clock() - t0
        # print("Elapsed time for SDA: %s seconds" %(time_elapsed))

    ##
    # Add mask based on union of all masks
    # \date       2017-02-03 16:46:33+0000
    #
    # \param      self                  The object
    # \param      mask_dilation_radius  The mask dilation radius
    # \param      mask_dilation_kernel  The kernel in "Ball", "Box", "Annulus"
    #                                   or "Cross"
    #
    def generate_mask_from_stack_mask_unions(self, mask_dilation_radius=0, mask_dilation_kernel="Ball"):

        # Define helpers to obtain averaged stack
        shape = sitk.GetArrayFromImage(self._HR_volume.sitk).shape
        array_mask = np.zeros(shape, dtype=np.uint8)

        # Average over domain specified by the joint mask ("union mask")
        for i in range(0, self._N_stacks):

            # Resample warped stack masks
            stack_sitk_mask = sitk.Resample(
                self._stacks[i].sitk_mask,
                self._HR_volume.sitk_mask,
                sitk.Euler3DTransform(),
                sitk.sitkNearestNeighbor,
                0,
                self._HR_volume.sitk_mask.GetPixelIDValue())

            # Get arrays of resampled warped stack and mask
            array_mask_tmp = sitk.GetArrayFromImage(stack_sitk_mask)

            # Sum intensities of stack and mask
            array_mask += array_mask_tmp

        # Create (joint) binary mask. Mask represents union of all masks
        array_mask[array_mask > 0] = 1

        HR_volume_mask_sitk = sitk.GetImageFromArray(array_mask)
        HR_volume_mask_sitk.CopyInformation(self._HR_volume.sitk)

        if mask_dilation_radius > 0:
            dilater = sitk.BinaryDilateImageFilter()
            dilater.SetKernelType(eval("sitk.sitk" + mask_dilation_kernel))
            dilater.SetKernelRadius(mask_dilation_radius)
            HR_volume_mask_sitk = dilater.Execute(HR_volume_mask_sitk)

        self._HR_volume = st.Stack.from_sitk_image(
            self._HR_volume.sitk, self._HR_volume.get_filename(), HR_volume_mask_sitk)

    ##
    # Add mask based on union of intersection of masks
    # \date       2017-02-03 16:46:33+0000
    #
    # \param      self                  The object
    # \param      mask_dilation_radius  The mask dilation radius
    # \param      mask_dilation_kernel  The kernel in "Ball", "Box", "Annulus"
    #                                   or "Cross"
    def generate_mask_from_stack_mask_intersections(self, mask_dilation_radius=0, mask_dilation_kernel="Ball"):

        # Define helpers to obtain averaged stack
        shape = sitk.GetArrayFromImage(self._HR_volume.sitk).shape
        array_mask = np.ones(shape, dtype=np.uint8)

        # Average over domain specified by the joint mask ("union mask")
        for i in range(0, self._N_stacks):

            # Resample warped stack masks
            stack_sitk_mask = sitk.Resample(
                self._stacks[i].sitk_mask,
                self._HR_volume.sitk_mask,
                sitk.Euler3DTransform(),
                sitk.sitkNearestNeighbor,
                0,
                self._HR_volume.sitk_mask.GetPixelIDValue())

            # Get arrays of resampled warped stack and mask
            array_mask_tmp = sitk.GetArrayFromImage(stack_sitk_mask)

            # Sum intensities of stack and mask
            array_mask *= array_mask_tmp

        # Create (joint) binary mask. Mask represents union of all masks
        array_mask[array_mask > 0] = 1

        HR_volume_mask_sitk = sitk.GetImageFromArray(array_mask)
        HR_volume_mask_sitk.CopyInformation(self._HR_volume.sitk)

        if mask_dilation_radius > 0:
            dilater = sitk.BinaryDilateImageFilter()
            dilater.SetKernelType(eval("sitk.sitk" + mask_dilation_kernel))
            dilater.SetKernelRadius(mask_dilation_radius)
            HR_volume_mask_sitk = dilater.Execute(HR_volume_mask_sitk)

        self._HR_volume = st.Stack.from_sitk_image(
            self._HR_volume.sitk, self._HR_volume.get_filename(), HR_volume_mask_sitk)

    # Recontruct volume based on discrete Shepard's like method, cf. Vercauteren2006, equation (19).
    #  The computation here is based on the YVV variant of Recursive Gaussian Filter and executed
    #  via ITK
    #  \remark Obtained intensity values are positive.
    def _run_discrete_shepard_reconstruction(self):

        shape = sitk.GetArrayFromImage(self._HR_volume.sitk).shape
        helper_N_nda = np.zeros(shape)
        helper_D_nda = np.zeros(shape)

        default_pixel_value = 0.0

        for i in range(0, self._N_stacks):
            # for i in range(0, 1):
            print("\tStack %s/%s" % (i, self._N_stacks-1))
            stack = self._stacks[i]
            slices = stack.get_slices()
            N_slices = stack.get_number_of_slices()

            # for j in range(10, 11):
            for j in range(0, N_slices):
                # print("\t\tSlice %s/%s" %(j,N_slices-1))
                slice = slices[j]
                slice_masked_sitk = slice.sitk * \
                    sitk.Cast(slice.sitk_mask, slice.sitk.GetPixelIDValue())

                # Nearest neighbour resampling of slice to target space (HR
                # volume)
                slice_resampled_sitk = sitk.Resample(
                    slice_masked_sitk,
                    self._HR_volume.sitk,
                    sitk.Euler3DTransform(),
                    sitk.sitkNearestNeighbor,
                    default_pixel_value,
                    self._HR_volume.sitk.GetPixelIDValue())

                # sitkh.show_sitk_image(slice_resampled_sitk)

                # Extract array of pixel intensities
                nda_slice = sitk.GetArrayFromImage(slice_resampled_sitk)

                # Get voxels in HR volume space which are stroke by the slice
                ind_nonzero = nda_slice > 0

                # update arrays of numerator and denominator
                helper_N_nda[ind_nonzero] += nda_slice[ind_nonzero]
                helper_D_nda[ind_nonzero] += 1

                # test = sitk.GetImageFromArray(helper_N_nda)
                # sitkh.show_sitk_image(test,title="N")

                # test = sitk.GetImageFromArray(helper_D_nda)
                # sitkh.show_sitk_image(test,title="D")

                # print("helper_N_nda: (min, max) = (%s, %s)" %(np.min(helper_N_nda), np.max(helper_N_nda)))
                # print("helper_D_nda: (min, max) = (%s, %s)" %(np.min(helper_D_nda), np.max(helper_D_nda)))

        # TODO: Set zero entries to one; Otherwise results are very weird!?
        helper_D_nda[helper_D_nda == 0] = 1

        # Create itk-images with correct header data
        pixel_type = itk.D
        dimension = 3
        image_type = itk.Image[pixel_type, dimension]

        itk2np = itk.PyBuffer[image_type]
        helper_N = itk2np.GetImageFromArray(helper_N_nda)
        helper_D = itk2np.GetImageFromArray(helper_D_nda)

        helper_N.SetSpacing(self._HR_volume.sitk.GetSpacing())
        helper_N.SetDirection(
            sitkh.get_itk_direction_from_sitk_image(self._HR_volume.sitk))
        helper_N.SetOrigin(self._HR_volume.sitk.GetOrigin())

        helper_D.SetSpacing(self._HR_volume.sitk.GetSpacing())
        helper_D.SetDirection(
            sitkh.get_itk_direction_from_sitk_image(self._HR_volume.sitk))
        helper_D.SetOrigin(self._HR_volume.sitk.GetOrigin())

        # Apply Recursive Gaussian YVV filter
        gaussian = itk.SmoothingRecursiveYvvGaussianImageFilter[
            image_type, image_type].New()   # YVV-based Filter
        # gaussian = itk.SmoothingRecursiveGaussianImageFilter[image_type,
        # image_type].New()    # Deriche-based Filter
        gaussian.SetSigmaArray(self._sigma_array)
        gaussian.SetInput(helper_N)
        gaussian.Update()
        HR_volume_update_N = gaussian.GetOutput()
        HR_volume_update_N.DisconnectPipeline()

        gaussian.SetInput(helper_D)
        gaussian.Update()
        HR_volume_update_D = gaussian.GetOutput()
        HR_volume_update_D.DisconnectPipeline()

        # Convert numerator and denominator back to data array
        nda_N = itk2np.GetArrayFromImage(HR_volume_update_N)
        nda_D = itk2np.GetArrayFromImage(HR_volume_update_D)

        # Compute data array of HR volume:
        # nda_D[nda_D==0]=1
        nda = nda_N/nda_D.astype(float)

        # Update HR volume image file within Stack-object HR_volume
        HR_volume_update = sitk.GetImageFromArray(nda)
        HR_volume_update.CopyInformation(self._HR_volume.sitk)

        # Link HR_volume.sitk to the updated volume
        self._HR_volume.sitk = HR_volume_update
        self._HR_volume.itk = sitkh.get_itk_from_sitk_image(HR_volume_update)

    # Recontruct volume based on discrete Shepard's like method, cf. Vercauteren2006, equation (19).
    #  The computation here is based on the Deriche variant of Recursive Gaussian Filter and executed
    #  via SimpleITK.
    #  \remark Obtained intensity values can be negative.
    def _run_discrete_shepard_based_on_Deriche_reconstruction(self):

        shape = sitk.GetArrayFromImage(self._HR_volume.sitk).shape
        helper_N_nda = np.zeros(shape)
        helper_D_nda = np.zeros(shape)

        default_pixel_value = 0.0

        for i in range(0, self._N_stacks):
            # for i in range(0, 2):
            print("  Stack %s/%s" % (i, self._N_stacks-1))
            stack = self._stacks[i]
            slices = stack.get_slices()
            N_slices = stack.get_number_of_slices()

            for j in range(0, N_slices):

                slice = slices[j]
                slice_masked_sitk = slice.sitk * \
                    sitk.Cast(slice.sitk_mask, slice.sitk.GetPixelIDValue())

                # Nearest neighbour resampling of slice to target space (HR
                # volume)
                slice_resampled_sitk = sitk.Resample(
                    slice_masked_sitk,
                    self._HR_volume.sitk,
                    sitk.Euler3DTransform(),
                    sitk.sitkNearestNeighbor,
                    default_pixel_value,
                    self._HR_volume.sitk.GetPixelIDValue())

                # Extract array of pixel intensities
                nda_slice = sitk.GetArrayFromImage(slice_resampled_sitk)

                # Look for indices which are stroke by the slice in the
                # isotropic grid
                ind_nonzero = nda_slice > 0

                # update arrays of numerator and denominator
                helper_N_nda[ind_nonzero] += nda_slice[ind_nonzero]
                helper_D_nda[ind_nonzero] += 1

                # print("helper_N_nda: (min, max) = (%s, %s)" %(np.min(helper_N_nda), np.max(helper_N_nda)))
                # print("helper_D_nda: (min, max) = (%s, %s)" %(np.min(helper_D_nda), np.max(helper_D_nda)))

        # TODO: Set zero entries to one; Otherwise results are very weird!?
        helper_D_nda[helper_D_nda == 0] = 1

        # Create sitk-images with correct header data
        helper_N = sitk.GetImageFromArray(helper_N_nda)
        helper_D = sitk.GetImageFromArray(helper_D_nda)

        helper_N.CopyInformation(self._HR_volume.sitk)
        helper_D.CopyInformation(self._HR_volume.sitk)

        # Apply recursive Gaussian smoothing
        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(self._sigma_array[1])

        HR_volume_update_N = gaussian.Execute(helper_N)
        HR_volume_update_D = gaussian.Execute(helper_D)

        # ## Avoid undefined division by zero
        # """
        # HACK start
        # """
        # ## HACK for denominator
        # nda = sitk.GetArrayFromImage(HR_volume_update_D)
        # ind_min = np.unravel_index(np.argmin(nda), nda.shape)
        # # print(nda[nda<0])
        # # print(nda[ind_min])

        # eps = 1e-8
        # # nda[nda<=eps]=1
        # print("denominator min = %s" % np.min(nda))

        # HR_volume_update_D = sitk.GetImageFromArray(nda)
        # HR_volume_update_D.CopyInformation(self._HR_volume.sitk)

        # ## HACK for numerator given that some intensities are negative!?
        # nda = sitk.GetArrayFromImage(HR_volume_update_N)
        # ind_min = np.unravel_index(np.argmin(nda), nda.shape)
        # # nda[nda<=eps]=0
        # # print(nda[nda<0])
        # print("numerator min = %s" % np.min(nda))
        # """
        # HACK end
        # """

        # Compute HR volume based on scattered data approximation with correct
        # header (might be redundant):
        HR_volume_update = HR_volume_update_N/HR_volume_update_D
        HR_volume_update.CopyInformation(self._HR_volume.sitk)

        # Update HR volume image file within Stack-object HR_volume
        self._HR_volume.sitk = HR_volume_update

        """
        Additional info
        """
        nda = sitk.GetArrayFromImage(HR_volume_update)
        print("Minimum of data array = %s" % np.min(nda))
