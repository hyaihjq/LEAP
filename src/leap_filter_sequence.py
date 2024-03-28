################################################################################
# Copyright 2022-2024 Lawrence Livermore National Security, LLC and other 
# LEAP project developers. See the LICENSE file for details.
# SPDX-License-Identifier: MIT
#
# LivermorE AI Projector for Computed Tomography (LEAP)
# filterSequence class
################################################################################
import numpy as np
from leapctype import *

class denoisingFilter:
    """ Parent class for denoising filters
    
    All filters (i.e., regularizers) must be written as a Python class which inherets this class.
    The apply function must be defined for all filters.  This function performs denoising of the given input.
    If the filter is differentiable, you must define cost, gradient, and quadForm functions.
    Nondifferentiable filters (e.g., median filter, bilateral filter, etc.) may also be defined, but can
    only be used by ASDPOCS.  On the other hand all differentiable filters can be used in any of the LEAP
    iterative reconstruction algorithms.
    
    """
    def __init__(self, leapct):
        """Constructor for denoisingFilter abstract class
        
        This defines three variables that shall be used by all denoising filters.
        leapct (object of the tomographicModels class): used to run algorithms from this class to carry out various filter implementations
        weight: this is the relative weight of a particular filter; only used by differentiable filters
        isDifferentiable (boolean): specifies whether the filter is differentiable or not
        
        """

        self.leapct = leapct
        self.weight = 1.0
        self.isDifferentiable = False
    
    def cost(self, f):
        """Calculates the cost of the given volume
        
        Args:
            f (C contiguous float32 numpy or torch array): volume data
            
        Returns:
            The cost (float) of the cost functional
        """
        pass
        
    def gradient(self, f):
        """Calculates the gradient of the given volume
        
        Args:
            f (C contiguous float32 numpy or torch array): volume data
            
        Returns:
            The gradient (C contiguous float32 numpy or torch array; has the same dimensions as the input) of the cost functional
        """
        pass
        
    def quadForm(self, f, d):
        """Calculates the quadratic form of the given volume and descent direction
        
        Args:
            f (C contiguous float32 numpy or torch array): volume data, current estimate
            d (C contiguous float32 numpy or torch array): volume data, descent direction
            
        Returns:
            The quadratic form (float) of the cost functional
        """
        pass
        
    def apply(self, f):
        """Filters (denoises) the input
        
        If this function is not defined in the child class, then this performs one gradient descent iteration
        as a means to apply the given filter.  This only works for differentiable filters.
        
        Args:
            f (C contiguous float32 numpy or torch array): volume data, current estimate
            
        Returns:
            The filtered (denoised) input (C contiguous float32 numpy or torch array, same dimensions as the input)
        """
        if self.isDifferentiable:
            d = self.gradient(f)
            num = self.leapct.sum(d**2)
            denom = self.quadForm(f, d)
            if denom <= 1.0e-16:
                return f
            stepSize = num / denom
            f -= stepSize * d
            return f
        else:
            return None

class BlurFilter(denoisingFilter):
    """This class defines a filter based on leapct.tomographicModels.BlurFilter which is a basic low pass filter
    
    Args:
        leapct (object of the tomographicModels class)
        FWHM (float): The Full Width at Half Maximum (given in number of pixels) of the low pass filter
    
    """
    def __init__(self, leapct, FWHM):
        super(BlurFilter, self).__init__(leapct)
        """Constructor for BlurFilter class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        FWHM (float): The Full Width at Half Maximum (given in number of pixels) of the low pass filter
        """

        self.FWHM = FWHM
        self.isDifferentiable = False
        
    def apply(self, f):
        return self.leapct.BlurFilter(f, self.FWHM)

class BilateralFilter(denoisingFilter):
    """This class defines a filter based on leapct.tomographicModels.BilateralFilter
    
    Args:
        leapct (object of the tomographicModels class)
        spatialFWHM (float): The Full Width at Half Maximum (given in number of pixels) of the filter
        intensityFWHM (float): The FWHM (given in the voxel value domain, which is usually mm^-1) of the filter
        scale (float): The FWHM of a low pass filter applied to the voxel values used in the intensity filter
    
    """
    def __init__(self, leapct, spatialFWHM, intensityFWHM, scale=1.0):
        super(BilateralFilter, self).__init__(leapct)
        """Constructor for BilateralFilter class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        spatialFWHM (float): The Full Width at Half Maximum (given in number of pixels) of the filter
        intensityFWHM (float): The FWHM (given in the voxel value domain, which is usually mm^-1) of the filter
        scale (float): The FWHM of a low pass filter applied to the voxel values used in the intensity filter
        """

        self.spatialFWHM = spatialFWHM
        self.intensityFWHM = intensityFWHM
        self.scale = scale
        self.isDifferentiable = False
        
    def apply(self, f):
        return self.leapct.BilateralFilter(f, self.spatialFWHM, self.intensityFWHM, self.scale)
        
class MedianFilter(denoisingFilter):
    """This class defines a filter based on leapct.tomographicModels.MedianFilter
    
    Args:
        leapct (object of the tomographicModels class)
        threshold (float): the threshold of whether to use the filtered value or not
        windowSize (int): the window size; can be 3 or 5
    
    """
    def __init__(self, leapct, threshold=0.0, windowSize=3):
        super(MedianFilter, self).__init__(leapct)

        self.threshold = threshold
        self.windowSize = windowSize
        self.isDifferentiable = False
        
    def apply(self, f):
        return self.leapct.MedianFilter(f, self.threshold, self.windowSize)

class TV(denoisingFilter):
    """This class defines a filter based on leapct anisotropic Total Variation (TV) regularizer
    
    Args:
        leapct (object of the tomographicModels class)
        delta (float): parameter for the Huber-like loss function used in TV
        weight (float): the regularizaion strength of this denoising filter term
        f_0 (C contiguous float32 numpy or torch array): a prior volume; this is optional but if specified this class calculates TV(f-f_0)
    
    """
    def __init__(self, leapct, delta=0.0, p=1.2, weight=1.0, f_0=None):
        super(TV, self).__init__(leapct)
        """Constructor for TV class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        delta (float): parameter for the Huber-like loss function used in TV
        weight (float): the regularizaion strength of this denoising filter term
        f_0 (C contiguous float32 numpy or torch array): a prior volume; this is optional but if specified this class calculates TV(f-f_0)
        """

        self.delta = delta
        self.p = max(0.01, p)
        self.weight = weight
        self.isDifferentiable = True
        self.f_0 = f_0
        
    def cost(self, f):
        """Calculates the anisotropic Total Variation functional of the given volume
        
        Args:
            f (C contiguous float32 numpy or torch array): volume data
            
        Returns:
            The cost (float) of the cost functional
        """
        if self.f_0 is not None:
            return self.leapct.TVcost(f-self.f_0, self.delta, self.weight, self.p)
        else:
            return self.leapct.TVcost(f, self.delta, self.weight, self.p)
        
    def gradient(self, f):
        if self.f_0 is not None:
            return self.leapct.TVgradient(f-self.f_0, self.delta, self.weight, self.p)
        else:
            return self.leapct.TVgradient(f, self.delta, self.weight, self.p)
        
    def quadForm(self, f, d):
        if self.f_0 is not None:
            return self.leapct.TVquadForm(f-self.f_0, d, self.delta, self.weight, self.p)
        else:
            return self.leapct.TVquadForm(f, d, self.delta, self.weight, self.p)
        
    def apply(self, f):
        if self.f_0 is not None:
            self.leapct.diffuse(f-self.f_0, self.delta, 1, self.p)
            f[:] += self.f_0[:]
            return f
        else:
            return self.leapct.diffuse(f, self.delta, 1, self.p)

class LpNorm(denoisingFilter):
    """This class defines a filter based on the L_p norm (raised to the p power) of the input
    
    Args:
        leapct (object of the tomographicModels class)
        p (float): The p-value of the L_p norm
        weight (float): the regularizaion strength of this denoising filter term
        f_0 (C contiguous float32 numpy or torch array): a prior volume; this is optional but if specified this class calculates ||f-f_0||_p^p
    """
    def __init__(self, leapct, p=1.0, weight=1.0, f_0=None):
        super(LpNorm, self).__init__(leapct)
        """Constructor for LpNorm class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        p (float): The p-value of the L_p norm
        weight (float): the regularizaion strength of this denoising filter term
        f_0 (C contiguous float32 numpy or torch array): a prior volume; this is optional but if specified this class calculates ||f-f_0||_p^p
        """
        
        self.p = max(0.0, p)
        self.weight = weight
        self.f_0 = f_0
        self.isDifferentiable = True
        
    def cost(self, f):
        if self.f_0 is not None:
            return self.weight * self.leapct.sum(self.leapct.abs(f-self.f_0)**self.p)
        else:
            return self.weight * self.leapct.sum(self.leapct.abs(f)**self.p)
        
    def gradient(self, f):
        Df = self.leapct.copyData(f)
        if self.f_0 is not None:
            Df[:] -= self.f_0[:]
        #    return self.p * self.leapct.sign(f-self.f_0) * self.leapct.abs(f-self.f_0)**(self.p-1.0)
        #else:
        #    return self.p * self.leapct.sign(f) * self.leapct.abs(f)**(self.p-1.0)
        Df = self.weight * self.p * self.leapct.sign(Df) * self.leapct.abs(Df)**(self.p-1.0)
        return Df
        
    def quadForm(self, f, d):
        if self.f_0 is not None:
            f_copy = self.leapct.copyData(f)
            f_copy[:] = f_copy[:] - self.f_0[:]
            ind = f_copy == 0.0
            f_copy[ind] = 1.0
            f_copy = self.leapct.abs(f_copy)**(self.p-2.0)
            f_copy[ind] = 0.0
            return self.weight * self.p * self.leapct.innerProd(f_copy, d, d)
        else:
            ind = f == 0.0
            f_copy = self.leapct.copyData(f)
            f_copy[ind] = 1.0
            f_copy = self.leapct.abs(f_copy)**(self.p-2.0)
            f_copy[ind] = 0.0
            return self.weight * self.p * self.leapct.innerProd(f_copy, d, d)

    def apply(self, f):
        if self.f_0 is not None:
            f[:] = f[:] - self.f_0[:]
            f = super().apply(f)
            f[:] += self.f_0[:]
            return f
        else:
            return super().apply(f)
        
class histogramSparsity(denoisingFilter):
    """This class defines a filter that encourages sparisty in the histogram domain
    
    Warning: this is a nonconvex regularizer.
    It is best to use this filter after an initial reconstruction is performed.
    
    Args:
        leapct (object of the tomographicModels class)
        mus (numpy array or list of floats): list of target values expected in the reconstruction volume
        weight (float): the regularizaion strength of this denoising filter term
    
    """
    def __init__(self, leapct, mus=None, weight=1.0):
        super(histogramSparsity, self).__init__(leapct)
        """Constructor for histogramSparsity class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        mus (numpy array or list of floats): list of target values expected in the reconstruction volume
        weight (float): the regularizaion strength of this denoising filter term
        """

        self.weight = weight
        self.isDifferentiable = True
        
        if type(mus) is not np.ndarray:
            mus = np.array(mus)
        if np.any(mus == 0.0) == False:
            mus = np.append(mus, 0.0)
        
        self.mus = np.sort(np.unique(mus))
        
        if mus.size > 1:
            minDist = np.abs(self.mus[1] - self.mus[0])
            for l in range(1,self.mus.size):
                minDist = min(minDist, np.abs(self.mus[l] - self.mus[l-1]))
            self.GemanParam = 0.25*minDist*minDist
        else:
            self.GemanParam = 1.0e-5

    def Geman0(self, x):
        return x*x/(x*x + self.GemanParam)

    def Geman1(self, x):
        return 2.0*self.GemanParam*x/((x*x + self.GemanParam)*(x*x + self.GemanParam))

    def Geman1_over_x(self, x):
        return 2.0*self.GemanParam/((x*x + self.GemanParam)*(x*x + self.GemanParam))
        
    def cost(self, f):
        curTerm = self.leapct.copyData(f)
        curTerm[:] = 1.0
        for l in range(self.mus.size):
            curTerm *= self.Geman0(f-self.mus[l])
        return self.weight * self.leapct.sum(curTerm)
        
    def gradient(self, f):
        Sp = self.leapct.copyData(f)
        Sp[:] = 0.0
        for l_1 in range(self.mus.size):
            curTerm = self.leapct.copyData(f)
            curTerm[:] = 1.0
            for l_2 in range(self.mus.size):
                if l_1 == l_2:
                    curTerm *= self.Geman1(f-self.mus[l_1])
                else:
                    curTerm *= self.Geman0(f-self.mus[l_2])
            Sp += curTerm
            Sp *= self.weight
        return Sp
        
    def quadForm(self, f, d):
        minDiff = self.leapct.copyData(f)
        minDiff[:] = self.leapct.abs(minDiff[:] - self.mus[0])
        for l in range(1,self.mus.size):
            minDiff = self.leapct.minimum(minDiff, self.leapct.abs(minDiff[:] - self.mus[l]))
        return self.weight * self.leapct.innerProd(self.Geman1_over_x(minDiff), d, d)

class azimuthalFilter(denoisingFilter):
    """This class defines a filter based on leapct AzimuthalBlur filter
    
    This denoising filter applies a high pass filter in the azimuthal direction of the reconstructed volume.
    If is useful for reconstructing objects that have a sparse azimuthal gradient, such as pipes with
    delaminations, voids, or high density inclusions.
    
    The functional is given by the L_p norm (raised to the p power) of the azimuthal high pass filter of the input,
    i.e., ||H(f)||_p^p, where H is the azimuthal high pass filter
    
    Args:
        leapct (object of the tomographicModels class)
        FWHM (float): The FWHM (measured in degrees) of the high pass filter
        p (float): the p-value of the L_p norm
        weight (float): the regularizaion strength of this denoising filter term
    """
    def __init__(self, leapct, FWHM, p, weight=1.0):
        super(azimuthalFilter, self).__init__(leapct)
        """Constructor for histogramSparsity class
        
        This constructor sets the following:
        leapct (object of the tomographicModels class)
        FWHM (float): The FWHM (measured in degrees) of the high pass filter
        p (float): the p-value of the L_p norm
        weight (float): the regularizaion strength of this denoising filter term
        """

        self.FWHM = FWHM
        self.p = p
        self.weight = weight
        self.isDifferentiable = True

    def cost(self, f):
        Bf = self.leapct.copyData(f)
        self.leapct.AzimuthalBlur(Bf, self.FWHM)
        Bf[:] = f[:] - Bf[:]
        return self.weight * self.leapct.sum(self.leapct.abs(Bf)**p)
        
    def gradient(self, f):
        Bf = self.leapct.copyData(f)
        self.leapct.AzimuthalBlur(Bf, self.FWHM)
        Bf[:] = f[:] - Bf[:]
        Bf = self.p * self.leapct.sign(Bf) * self.leapct.abs(Bf)**(self.p-1.0)
        
        BBf = self.leapct.copyData(Bf)
        self.leapct.AzimuthalBlur(BBf, self.FWHM)
        Bf[:] = Bf[:] - BBf[:]
        Bf *= self.weight
        return Bf
        
    def quadForm(self, f, d):
        Bf = self.leapct.copyData(f)
        self.leapct.AzimuthalBlur(Bf, self.FWHM)
        Bf[:] = f[:] - Bf[:]
        Bd = self.leapct.copyData(d)
        self.leapct.AzimuthalBlur(Bd, self.FWHM)
        Bd[:] = d[:] - Bd[:]
        
        ind = Bf == 0.0
        Bf[ind] = 1.0
        Bf = self.leapct.abs(Bf)**(self.p-2.0)
        Bf[ind] = 0.0
        
        return self.weight * self.p * self.leapct.innerProd(Bf, Bd, Bd)
        
class filterSequence:
    """This class defines a weighted sum of filters (i.e., regularizers)
    
    Args:
        beta (float): the overall strength of the sequence of filters, if zero no filters are applied
    
    """
    def __init__(self, beta=1.0):
        """Constructor for the filterSequence class
        
        This constructor sets the following:
        beta (float): the overall strength of the sequence of filters, if zero no filters are applied
        """
        self.filters = []
        self.beta = beta

    def append(self, newFilter):
        """Append a new filter to the list
        
        Note that in the case of ASDPOCS, the order of the sequence of filters matters because they are applied sequentially.
        When used in a gradient-based algorithm, the cost of filter sequence is given by
        self.beta * sum_n filters[n].cost(f)
        and note that each filter can have its own weight, given by filters[n].weight
        
        Args:
            newFilter (object whose base class is denoisingFilter): the denoising filter to add to the sequence of filters
        
        """
        self.filters.append(newFilter)
        
    def clear(self):
        """Removes all filters from the list"""
        self.filters = []
        
    def cost(self, f):
        """Calculates the accumulated cost of all filters"""
        retVal = 0.0
        if self.beta > 0.0:
            for n in range(len(self.filters)):
                if self.filters[n].isDifferentiable == True and self.filters[n].weight > 0.0:
                    retVal += self.filters[n].cost(f)
            retVal *= self.beta
        return retVal
        
    def gradient(self, f):
        """Calculates the accumulated gradient of all filters"""
        D = self.filters[0].leapct.copyData(f)
        D[:] = 0.0
        if self.beta > 0.0:
            for n in range(len(self.filters)):
                if self.filters[n].isDifferentiable == True and self.filters[n].weight > 0.0:
                    D += self.filters[n].gradient(f)
            D *= self.beta
        return D
        
    def quadForm(self, f, d):
        """Calculates the accumulated quadratic form of all filters"""
        retVal = 0.0
        if self.beta > 0.0:
            for n in range(len(self.filters)):
                if self.filters[n].isDifferentiable == True and self.filters[n].weight > 0.0:
                    retVal += self.filters[n].quadForm(f,d)
            retVal *= self.beta
        return retVal
        
    def apply(self, f):
        """Applies all the filters in sequence"""
        for n in range(len(self.filters)):
            self.filters[n].apply(f)
        return f
