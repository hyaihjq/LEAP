import sys
import os
import time
import numpy as np
from leapctype import *
leapct = tomographicModels()
sys.path.append(r'..\utils')
from generateDictionary import *

'''
This sample script demonstrates how one can perform dictionary denoising.
The dictionary elements must be 3D numpy arrays.  2D dictionary elements are possible
by making one of the three dimensions be of size 1
We provide some sample dictionaries, but you can supply your own dictionary.
The dictionaries we currently supply are complete (not overcomplete) and we are working on good
overcomplete dictionaries which we will include in future releases.
If the dictionary is complete and orthonormal, the algorithm runs about 2-8 times faster.
'''


# Specify the number of detector columns which is used below
# Scale the number of angles and the detector pixel size with N
numCols = 512
numAngles = 2*2*int(360*numCols/1024)
pixelSize = 0.65*512/numCols

# Set the number of detector rows
#numRows = numCols
numRows = 8

# Set the scanner geometry
leapct.set_conebeam(numAngles, numRows, numCols, pixelSize, pixelSize, 0.5*(numRows-1), 0.5*(numCols-1), leapct.setAngleArray(numAngles, 360.0), 1100, 1400)
#leapct.set_curvedDetector()

# Set the volume parameters.
# It is best to do this after the CT geometry is set
leapct.set_default_volume()

# If you want to specify the volume yourself, use this function:
#leapct.set_volume(numX, numY, numZ, voxelWidth=None, voxelHeight=None, offsetX=None, offsetY=None, offsetZ=None):

# Trouble-Shooting Functions
leapct.print_parameters()
#leapct.sketch_system()

# Allocate space for the projections and the volume
# You don't have to use these functions; they are provided just for convenience
# All you need is for the data to be C contiguous float32 arrays with the right dimensions
g = leapct.allocateProjections() # shape is numAngles, numRows, numCols
f = leapct.allocateVolume() # shape is numZ, numY, numX

# Specify simplified FORBILD head phantom
# One could easily do this in Python, but Python is soooooo slow for these types of operations,
# so we implemented this feature with multi-threaded C++
leapct.set_FORBILD(f,True)
#leapct.display(f)


# "Simulate" projection data
startTime = time.time()
leapct.project(g,f)
print('Forward Projection Elapsed Time: ' + str(time.time()-startTime))
#leapct.display(g)

# Add noise to the data (just for demonstration purposes)
I_0 = 10000.0
t = np.random.poisson(I_0*np.exp(-g))
t[t<1.0] = 1.0
g[:] = -np.log(t/I_0)

# Reset the volume array to zero, otherwise iterative reconstruction algorithm will start their iterations
# with the true result which is cheating
f[:] = 0.0

# Reconstruct the data
startTime = time.time()
leapct.FBP(g,f)
print('Reconstruction Elapsed Time: ' + str(time.time()-startTime))

#D = generateRidgeletDictionary(8) # This one does not work so well and needs improvement
#D = generateDCTDictionary(8)
#D = generateDCTDictionary(4,True)
#D = generateLegendreDictionary(8)
D = generateLegendreDictionary(4,True)
#print(D.shape)


# Run Dictionary Denoising
startTime = time.time()
f_0 = f.copy()
#leapct.DictionaryDenoising(f, D, 12, 0.0002)
#leapct.DictionaryDenoising(f, D, 12, 0.002)
leapct.DictionaryDenoising(f, D, 4, 0.002)
#leapct.DictionaryDenoising(f, D, 12, 0.002)
print('Post-Processing Elapsed Time: ' + str(time.time()-startTime))


# Display a slice before and after the dictionary denoising
f_0_slice = np.squeeze(f_0[f.shape[0]//2,:,:])
f_slice = np.squeeze(f[f.shape[0]//2,:,:])
I = np.concatenate((f_0_slice, f_slice),axis=1)
I[I<0.0] = 0.0
I[I>0.04] = 0.04

import matplotlib.pyplot as plt
plt.imshow(I, cmap='gray')
plt.show()

