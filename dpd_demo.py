#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This program is part of pyHNC, copyright (c) 2023 Patrick B Warren (STFC).
# Email: patrick.warren{at}stfc.ac.uk.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

# Demonstrate the capabilities of the HNC package for solving DPD
# potentials, comparing with SunlightHNC if requested, and plotting
# the pair distribution function and the structure factor too.  For
# details here see also the SunlightHNC documentation.

# For standard DPD at A = 25 and ρ = 3, we have the following table

#           ∆t = 0.02   ∆t = 0.01   Monte-Carlo  HNC   deviation
# pressure  23.73±0.02  23.69±0.02  23.65±0.02   23.564  (0.4%)
# energy    13.66±0.02  13.64±0.02  13.63±0.02   13.762  (1.0%)
# mu^ex     12.14±0.02  12.16±0.02  12.25±0.10   12.171  (0.7%)

# The first two columns are from dynamic simulations.  The excess
# chemical potential (final row) is measured by Widom insertion in the
# simulations and calculated by SunlightHNC.  The pressure end energy
# density are from SunlightHNC and the present code and are in
# agreement to at least the indicated number of decimals.  The
# deviation is between HCNC and simulation results.

# Data is from a forthcoming publication on osmotic pressure in DPD.

import argparse
import numpy as np
from numpy import pi as π
from pyHNC import Grid, PicardHNC, add_grid_args, grid_args, add_solver_args, solver_args, truncate_to_zero

parser = argparse.ArgumentParser(description='DPD HNC calculator')
add_grid_args(parser)
add_solver_args(parser)
parser.add_argument('--A', action='store', default=25.0, type=float, help='repulsion amplitude, default 25.0')
parser.add_argument('--rho', action='store', default=3.0, type=float, help='density, default 3.0')
parser.add_argument('--rmax', action='store', default=3.0, type=float, help='maximum in r for plotting, default 3.0')
parser.add_argument('--qmax', action='store', default=25.0, type=float, help='maximum in q for plotting, default 25.0')
parser.add_argument('--sunlight', action='store_true', help='compare to SunlightHNC')
parser.add_argument('--show', action='store_true', help='show results')
args = parser.parse_args()

A, ρ = args.A, args.rho

grid = Grid(**grid_args(args)) # make the initial working grid

r, Δr, q = grid.r, grid.deltar, grid.q # extract the co-ordinate arrays for use below

# Define the DPD potential, and its derivative, then solve the HNC
# problem.  The arrays here are all size ng-1, same as r[:]

φ = truncate_to_zero(A/2*(1-r)**2, r, 1) # the DPD potential
f = truncate_to_zero(A*(1-r), r, 1) # the force f = -dφ/dr

solver = PicardHNC(grid, **solver_args(args))
soln = solver.solve(φ, ρ) # solve for the DPD potential
hr, hq = soln.hr, soln.hq # extract for use in a moment

# For the integrals here, see Eqs. (2.5.20) and (2.5.22) in
# Hansen & McDonald, "Theory of Simple Liquids" (3rd edition):
# for the (excess) energy density, e = 2πρ² ∫_0^∞ dr r² φ(r) g(r) 
# and virial pressure, p = ρ + 2πρ²/3 ∫_0^∞ dr r³ f(r) g(r)
# where f(r) = −dφ/dr is the force.

# The constant terms here capture the mean field contributions, that
# is the integrals evaluated with g(r) = 1.  Specifically:
# ∫_0^∞ dr r² φ(r) = A/2 ∫_0^1 dr r² (1−r)² = A/60 ;
# ∫_0^∞ dr r³ f(r) = A ∫_0^1 dr r³ (1−r) = A/20 .

e = 2*π*ρ**2 * (A/60 + np.trapz(r**2*φ*hr, dx=Δr))
p = ρ + 2*π*ρ**2/3 * (A/20 + np.trapz(r**3*f*hr, dx=Δr))

print('Model: standard DPD with A = %f, ρ = %f' % (A, ρ))

if A == 25 and ρ == 3:
    print('Monte-Carlo:   energy density, virial pressure =\t\t13.63±0.02\t23.65±0.02')
print('pyHNC v%s:    energy density, virial pressure =\t\t%0.5f\t%0.5f' % (grid.version, e, p))

if args.sunlight:
    
    from oz import wizard as w

    w.initialise()
    w.arep[0,0] = A
    w.dpd_potential()
    w.rho[0] = ρ
    w.hnc_solve()
    
    version = str(w.version, 'utf-8').strip()
    print('SunlightHNC v%s: energy density,  virial pressure =\t\t%0.5f\t%0.5f' % (version, w.uex, w.press))

if args.show:

    import matplotlib.pyplot as plt

    gr = 1.0 + hr # the pair function
    sq = 1.0 + ρ*hq # the structure factor

    plt.figure(1)
    cut = r < args.rmax
    if args.sunlight:
        imax = int(args.rmax / w.deltar)
        plt.plot(w.r[0:imax], 1.0+w.hr[0:imax,0,0], '.')
        plt.plot(r[cut], gr[cut], '--')
    else:
        plt.plot(r[cut], gr[cut])        
    plt.xlabel('$r$')
    plt.ylabel('$g(r)$')

    plt.figure(2)
    cut = q < args.qmax
    if args.sunlight:
        jmax = int(args.qmax / w.deltak)
        plt.plot(w.k[0:jmax], w.sk[0:jmax,0,0]/ρ, '.')
        plt.plot(q[cut], sq[cut], '--')
    else:
        plt.plot(q[cut], sq[cut])
    plt.xlabel('$k$')
    plt.ylabel('$S(k)$')

    plt.show()
