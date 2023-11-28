////////////////////////////////////////////////////////////////////////////////
// Copyright 2022-2023 Lawrence Livermore National Security, LLC and other 
// LEAP project developers. See the LICENSE file for details.
// SPDX-License-Identifier: MIT
//
// LivermorE AI Projector for Computed Tomography (LEAP)
// cuda header for Joseph projector
////////////////////////////////////////////////////////////////////////////////

#ifndef __PROJECTORS_JOSEPH_H
#define __PROJECTORS_JOSEPH_H

#ifdef WIN32
#pragma once
#endif

#include "parameters.h"

bool project_Joseph(float*&, float*, parameters*, bool cpu_to_gpu);
bool backproject_Joseph(float*, float*&, parameters*, bool cpu_to_gpu);

bool project_Joseph_modular(float*&, float*, parameters*, bool cpu_to_gpu);
bool backproject_Joseph_modular(float*, float*&, parameters*, bool cpu_to_gpu);

#endif
