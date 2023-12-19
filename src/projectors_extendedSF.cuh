////////////////////////////////////////////////////////////////////////////////
// Copyright 2022-2023 Lawrence Livermore National Security, LLC and other 
// LEAP project developers. See the LICENSE file for details.
// SPDX-License-Identifier: MIT
//
// LivermorE AI Projector for Computed Tomography (LEAP)
// cuda module header for projectors with voxel sizes that are
// much smaller or much larger than the nominal sizes
////////////////////////////////////////////////////////////////////////////////

#ifndef __PROJECTORS_EXTENDEDSF_H
#define __PROJECTORS_EXTENDEDSF_H

#ifdef WIN32
#pragma once
#endif

#include "parameters.h"

bool project_eSF(float*&, float*, parameters*, bool data_on_cpu);
bool backproject_eSF(float*, float*&, parameters*, bool data_on_cpu);

bool project_eSF_fan(float*&, float*, parameters*, bool data_on_cpu);
bool backproject_eSF_fan(float*, float*&, parameters*, bool data_on_cpu);

bool project_eSF_cone(float*&, float*, parameters*, bool data_on_cpu);
bool backproject_eSF_cone(float*, float*&, parameters*, bool data_on_cpu);

bool project_eSF_parallel(float*&, float*, parameters*, bool data_on_cpu);
bool backproject_eSF_parallel(float*, float*&, parameters*, bool data_on_cpu);

#endif
