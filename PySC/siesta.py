#!/usr/bin/env python
import sys,os,shutil
from math import *
from chem_utils import *
from struct_utils import * 
mod_name = 'siesta.py'

def f_siesta_create_fdf(name):
  sname = "f_siesta_create_fdf"

  ofile = open(name.strip()+".fdf",'w')
  print "Create new SIESTA fdf: "+name.strip()+".fdf"

  # check the number of species
  ofile.write("# SIESTA fdf file generated by %s @ %s\n" %(sname,mod_name))
  ofile.write("\n# system info\n")
  ofile.write("SystemName %s\n"  %(name))
  ofile.write("SystemLabel %s\n" %(name))

  ofile.write("""
#! General parameters
UseSaveData yes

#! relaxation paramters
MD.NumCGsteps 0                    # the number of steps for structural optimization
MD.TypeOfRun  cg
#MD.VariableCell yes

#! XC functional  
XC.functional GGA       #!!! always try to use same xc functionalf for generating pseudopotential  
XC.authors PBE          

#! Basis set parameters
PAO.EnergyShift  50 meV
PAO.BasisSize    DZP

#! spin-polarized case 
#SpinPolarized yes
#FixSpin yes       #! 
#TotalSpin 1.0     #! imposed total spin polarization of the system (in units of the electron spin, 1/2)
#%block DM.InitSpin
#   1   1.0         # Atom index, spin
#   2  -1.0    
#%endblock DM.InitSpin
 
#! SCF parameters
MaxSCFIterations 500
DM.NumberPulay 6
DM.MixingWeight 0.25               # reduce this number for difficcult cases, but not too small
SCFMustConverge .true.

# uncomment the followings if you need very accurate total energies
#DM.Tolerance 1.e-5                     #  the default 1.e-4              
#DM.Require.Energy.Convergence  .true.  # .false.
#DM.Energy.Tolerance  1.e-5 eV          # 1.e-4 eV

# for metallic systems 
# ElectronicTemperature 300.0 K      # increases this for difficult cases
# OccupationFunction FD              # changing to MP may be helpful for difficult cases
# OccupationMPOrder 4                # effective only for OccupationFunction=MP

#! Output options
#SaveElectrostaticPotential yes    # needed for workfunction
#SaveDeltaRho               yes    # total density minus overlapped atomic density
WriteCoorXmol               yes    # write molecular structure in the SystemLabel.xyz
WriteMullikenPop            1
  """)
  ofile.write("\n")
  ofile.close()


# write lattice structure into the siesta format
def f_siesta_write_struct(name,mol,latt_const=None,latt_vec=None,full_fdf=True):
  """
  Write the crystal structure information to the siesta fdf format 
  """
  sname = "f_Write_Struct_siesta"
  
  fdf = name.strip()+".fdf"
  if full_fdf is True:
    f_siesta_create_fdf(name)
    ofile = open(name.strip()+".fdf",'a')
  else:
    ofile = open(fdf,'w')

  # check the number of species 
  nat = len(mol)
  nsp,nat_sp,species,sp_index = f_Check_Species(mol)

  ofile.write("# SIESTA fdf file generated by %s @ %s\n" %(sname,mod_name))
 
  ofile.write("\n# structural information \n")
  ofile.write("\nNumberOfAtoms\t %6d\n" %(nat))
  ofile.write("NumberOfSpecies\t %6d\n" %(nsp))

  ofile.write("%block ChemicalSpeciesLabel\n")
  for isp in range(nsp):
    znucl= f_Element_Symbol_to_Z(species[isp])
    ofile.write("%6d\t%6d\t%6s\n"%(isp+1,znucl,species[isp]))
  ofile.write("%endblock ChemicalSpeciesLabel\n\n") 

  if latt_const is None: 
    xyz_scale = 1.0 
    ofile.write("AtomicCoordinatesFormat\t Ang\n")
  else: 
    a0=latt_const
    ofile.write("LatticeConstant\t %12.6f Ang\n"%(a0))
    ofile.write("kgrid_cutoff\t %12.6f Ang\n\n"%(a0*2))
    ofile.write("%block LatticeVectors\n")
    for i in range(3): 
      ofile.write("%10.6f %10.6f %10.6f\n"%(latt_vec[i][0]/a0,latt_vec[i][1]/a0,latt_vec[i][2]/a0))
    ofile.write("%endblock LatticeVectors\n\n")

    xyz_scale = 1.0
    ofile.write("AtomicCoordinatesFormat\t Fractional \n")

  ofile.write("%block AtomicCoordinatesAndAtomicSpecies\n")
  for iat in range(nat):
    xyz  = mol[iat][1][:]
    for i in range(3): xyz[i] /= xyz_scale 
    atom = mol[iat][0]
    isp = sp_index[iat]
    ofile.write("%12.6f %12.6f %12.6f %6d # %6s %6d\n" %(xyz[0],xyz[1],xyz[2],isp,atom,iat+1))
  ofile.write("%endblock AtomicCoordinatesAndAtomicSpecies\n\n")

  ofile.close()

def f_siesta_read_structout(name,type='m'):
  """
  Read structure information from name.STRUCT_OUT 
  """
  ifile = open(name.strip()+".STRUCT_OUT",'r')
 
  # read lattice vectors
  latt_vec=[]
  for i in range(3):
    line = ifile.readline().split()
    vec=[]
    for j in range(3): 
      vec.append(float(line[j]))
    latt_vec.append(vec) 

  # get the number of atoms 
  line = ifile.readline()   
  natom = int(line)

  mol=[]
  for ia in range(natom): 
    line = ifile.readline().split()
    znuc = int(line[1]) 
    atom = f_Element_Z_to_Symbol(znuc)
    xyz = [float(line[2]),float(line[3]),float(line[4])]

    if type == 'm': ## a molecule structure is read 
      xyz_old = xyz[:]
      xyz = [0.0, 0.0, 0.0]
      for j in range(3):
        for i in range(3):  
          xyz[j] += xyz_old[i]*latt_vec[i][j]
    mol.append([atom,xyz])

  if type == 'm':
    return mol
  else:
    return mol,latt_vec
