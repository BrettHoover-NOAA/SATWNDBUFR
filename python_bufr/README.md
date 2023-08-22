**Importing BUFR query into your own conda environment**
This is a little involved, so I figured I’d outline the process verbosely. The version of python that was used to build ioda-bundle needs to be used in your own conda environment. The easiest way to find it is to look at /path/to/ioda-bundle/build/CMakeCache.txt:  
  
`PYBIND11_PYTHON_EXECUTABLE_LAST:INTERNAL=/usr/bin/python3.6`  
  
If I look at the version:  
`/usr/bin/python3.6 --version`  
I see the message:  
`Python 3.6.8`  
  
When setting up my environment.yml file, I specify this precise version of python along with the other packages I am interested in. I also specify conda-build, which will be used after building the environment:  
  
`name: python_bufr`  
`channels:`  
`  - defaults`  
`dependencies:`  
`  - python=3.6.8`  
`  - numpy`  
`  - matplotlib`  
`  - netcdf4`  
`  - cartopy`  
`  - jupyter`  
`  - conda-build`  
  
I am using my own version of miniconda3 on Hera in tcsh. I made conda available for tcsh via the command:  
  
`<path to miniconda>/bin/conda init tcsh`  
  
Which generated a block of code in ~/.tcshrc to add conda to PATH. After exiting and restarting the terminal, conda was available for use on tcsh.  
  
`conda env create --file environment.yml`  
  
After the environment is generated, activate it:  
  
`conda activate python_bufr`  
  
We need to now link the pyioda subdirectory of /path/to/ioda-bundle/build/lib/python{x.y}/pyioda subdirectory. A search reveals the subdirectory is in:  
  
/path/to/ioda-bundle/build/lib/python3.6/pyioda/  
  
With the environment loaded, issue the following command:  
  
`conda-develop /path/to/ioda-bundle/build/lib/python3.6/pyioda/  
  
You will see a message (probably with a warning that the command will change to conda develop, without the hyphen, in a future release) that the operation is completed:  
  
`added /path/to/ioda-bundle/build/lib/python3.6/pyioda`  
`completed operation for: /path/to/ioda-bundle/build/lib/python3.6/pyioda`  
  
This is accomplished by generating the conda.pth file in /path/to/conda/environment/python_bufr/lib/python3.6/site-packages/conda.pth, which contains a single line specifying the full-path to the /pyioda directory. This is similar in form to the instructions given in /path/to/ioda-bundle/README.md for setting up Python API in pycharm.  
  
Now you can access the bufr.cpython.{...} object in your own miniconda environment, as long as you use the BUFR/hera modulefile included in this package.  
