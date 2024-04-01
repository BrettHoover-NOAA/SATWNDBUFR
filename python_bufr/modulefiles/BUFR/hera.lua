help([[
Load environment for running the BUFR application with python and MPI.
]])

local pkgName    = myModuleName()
local pkgVersion = myModuleVersion()
local pkgNameVer = myModuleFullName()

conflict(pkgName)

prepend_path("MODULEPATH", '/scratch1/NCEPDEV/nems/role.epic/spack-stack/spack-stack-1.6.0/envs/unified-env-rocky8/install/modulefiles/Core')
prepend_path("MODULEPATH", '/scratch1/NCEPDEV/da/python/opt/modulefiles/stack')

-- below two lines get us access to the spack-stack modules
load("stack-intel/2021.5.0")
load("stack-intel-oneapi-mpi/2021.5.1")
-- need libeckit.so, libbufr_4.so
load("eckit/1.24.5")
load("bufr/12.0.1")

setenv("CC","mpiicc")
setenv("FC","mpiifort")
setenv("CXX","mpiicpc")

local mpiexec = '/apps/slurm/default/bin/srun'
local mpinproc = '-n'
setenv('MPIEXEC_EXEC', mpiexec)
setenv('MPIEXEC_NPROC', mpinproc)


whatis("Name: ".. pkgName)
whatis("Version: ".. pkgVersion)
whatis("Category: BUFR")
whatis("Description: Load all libraries needed for BUFR")
