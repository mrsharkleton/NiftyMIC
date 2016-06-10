/*! \brief Code to verify the implementation of itkAdjointOrientedGaussianInterpolateImageFilter.
 *
 *  
 *
 *  \author Michael Ebner (michael.ebner.14@ucl.ac.uk)
 *  \date February 2016
 */

#ifndef MYITKIMAGEHELPER_H_
#define MYITKIMAGEHELPER_H_

#include <string>
#include <limits.h>     /* PATH_MAX */
#include <math.h>
#include <cstdlib>     /* system, NULL, EXIT_FAILURE */

#include <itkImage.h>
#include <itkImageFileReader.h>
#include <itkImageFileWriter.h>
#include <itkNiftiImageIO.h>
#include <itkResampleImageFilter.h>
#include <itkImageRegionIteratorWithIndex.h>

//#include "ImageFactory.h"

/** Typedefs. */
typedef double PixelType;
typedef unsigned char MaskPixelType;

typedef itk::Image< PixelType, 2 >  ImageType2D;
typedef itk::Image< PixelType, 3 >  ImageType3D;
typedef itk::Image< MaskPixelType, 2 >  MaskImageType2D;
typedef itk::Image< MaskPixelType, 3 >  MaskImageType3D;

// typedef itk::ImageFileReader< ImageType2D >  ReaderType2D;
// typedef itk::ImageFileReader< ImageType3D >  ReaderType3D;
// typedef itk::ImageFileReader< MaskImageType2D >  MaskReaderType2D;
// typedef itk::ImageFileReader< MaskImageType3D >  MaskReaderType3D;

// typedef itk::ImageFileWriter< ImageType2D >  WriterType2D;
// typedef itk::ImageFileWriter< ImageType3D >  WriterType3D;
// typedef itk::ImageFileWriter< MaskImageType2D >  MaskWriterType2D;
// typedef itk::ImageFileWriter< MaskImageType3D >  MaskWriterType3D;


class MyITKImageHelper {

public:

    /** Show image */
    static void showImage(const ImageType2D::Pointer image, const std::string &filename = "image");
    static void showImage(const MaskImageType2D::Pointer image, const std::string &filename = "segmentation");
    static void showImage(const ImageType2D::Pointer image, const ImageType2D::Pointer overlay, const std::string &filename = "image+overlay");
    static void showImage(const ImageType2D::Pointer image, const MaskImageType2D::Pointer segmentation, const std::string &filename = "image+segmentation");

    static void showImage(const ImageType3D::Pointer image, const std::string &filename = "image");
    static void showImage(const MaskImageType3D::Pointer image, const std::string &filename = "segmentation");
    static void showImage(const ImageType3D::Pointer image, const ImageType3D::Pointer overlay, const std::string &filename = "image+overlay");
    static void showImage(const ImageType3D::Pointer image, const MaskImageType3D::Pointer segmentation, const std::string &filename = "image+segmentation");

    /** Read image */
    template <typename ImageType>
    static const typename ImageType::Pointer readImage(const std::string &filename);

    /** Write image */
    static void writeImage(const ImageType2D::Pointer image, const std::string &filename);
    static void writeImage(const MaskImageType2D::Pointer image, const std::string &filename);
    static void writeImage(const ImageType3D::Pointer image, const std::string &filename);
    static void writeImage(const MaskImageType3D::Pointer image, const std::string &filename);

    /** Get data array */
    // static 
};

#include "MyITKImageHelper.tpp"

#endif  /* MYITKIMAGEHELPER_H_ */