#!/usr/bin/env python

from __future__ import print_function
from future.utils import with_metaclass
from builtins import range
from builtins import object
import os
import argparse
import numpy as np
#Do these as absolute imports instead of relative as
#we may want to run this program as a script directly.
from cosmosis.postprocessing import lazy_pylab as pylab
from cosmosis.runtime import utils


#Set up the command line arguments
parser = argparse.ArgumentParser(description="""
This script makes some standard plots based on a directory of CosomoSIS output
for a single set of cosmological parameters, as generated by the "test" sampler
in CosmoSIS.  Have a look at the first demo we have for an example.

You need to supply at least the name of the directory where CosmoSIS data was
saved.

You can either call this script directly or use the "postprocess" program on the
ini file.
""")

parser.add_argument("dirname", help="A directory of cosmology data as produced by the 'test' sampler")
parser.add_argument("-o", "--output_dir", default=".", help="The directory in which to put the plots")
parser.add_argument("-p", "--prefix", default="", help="A filename prefix for all the plots")
parser.add_argument("-t", "--type", default="png", help="Image file type suffix")


# Okay, here is the structure of this script.  We have a base Plot class which
# handles finding the data files, working out filenames, and saving plots.  The
# subclasses are then in charge of the plot contents.

# The Plot class also uses a metaclass to register its subclasses
# so that there is less plumbing to do when adding a new plot.

class RegisteredPlot(type):
    registry = set()
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        meta.registry.add(cls)
        meta.registry -= set(bases)
        return cls

class Plot(with_metaclass(RegisteredPlot, object)):
    #Subclasses should override this to specify the base
    #part of their filename
    filename = "error"

    def __init__(self, dirname, outdir, prefix, suffix,
             quiet=False, figure=None):
        #Set up the plotting figure
        if figure is None:
            self.figure = pylab.figure()
        else:
            self.figure = figure

        #Can do prefixes if we want to all the filenames
        if prefix:
            prefix += "_"

        # We have an output directory, a prefix, base filename (which is
        # overridden by subclasses) And a suffix (file type).
        self.outfile = (outdir + "/" + prefix + self.filename
                    + "." + suffix)

        #All the data will be in subclasses of this
        self.dirname = dirname
        self.quiet=quiet

    def file_path(self, section, name):
        return self.dirname + "/" + section + "/" + name + ".txt"

    def load_file(self, section, name):
        "Load a data file from the directory of saved theory data"
        #Find the filename and load it
        filename = self.file_path(section, name)
        try:
            return np.loadtxt(filename)
        except Exception as e:
            raise IOError("Not making plot: %s (no data in this sample)"% self.__class__.__name__[:-4])

    #Handy little method for trying to numeric-ify a value
    @staticmethod
    def try_numeric(value):
        try:
            return float(value)
        except:
            pass
        try:
            return int(value)
        except:
            pass
        return value

    # The scalar parameters in the DataBlock are saved to a
    # file called values.txt for each section.
    # This file loads that values file into a dictionary
    def load_values(self, section):
        filename = self.dirname + "/" + section + "/values.txt"
        values = {}
        for line in open(filename):
            line=line.strip()
            if not line:
                continue
            name, value = line.split('=')
            values[name.strip()] = self.try_numeric(value.strip())
        return values

    #Base method - subclasses should call this super method
    #and then override to supply their own plot content
    def plot(self):
        pylab.figure(self.figure.number)

    #Need not be over-ridden
    def save(self):
        pylab.figure(self.figure.number)
        if not self.quiet: print("Saving ", self.outfile)
        pylab.savefig(self.outfile)

    #Need not be overridden. Called by the main function
    @classmethod
    def make(cls, dirname, outdir, prefix, suffix):
        p = cls(dirname, outdir, prefix, suffix)
        p.plot()
        p.save()
        return p.filename



class DistancePlot(Plot):
    "Subclasses of this do distance plots as a function of z"
    scaling=1.0
    def plot(self):
        super(DistancePlot, self).plot()
        z = self.load_file("distances", "z")
        d = self.load_file("distances", self.distance)
        pylab.plot(z, d*self.scaling)
        pylab.grid()
        pylab.xlabel("Redshift z")
        pylab.ylabel(self.name)



class AngularDiameterDistancePlot(DistancePlot):
    distance = "d_a"
    filename = "angular_distance"
    name = "Angular Diameter Distance $D_A / Mpc$"

class LuminosityDistancePlot(DistancePlot):
    distance = "d_l"
    filename = "luminosity_distance"
    name = "Luminosity Distance $D_L / Mpc$"

class ComovingDistancePlot(DistancePlot):
    distance = "d_m"
    filename = "comoving_distance"
    name = "Comoving Distance $D_L / Mpc$"

class HubblePlot(DistancePlot):
    distance = "h"
    filename = "hubble"
    name = "Hubble Parameter $H(z) / (km/s/Mpc)$"
    scaling = 2.99792458e+05

class DistanceModulusPlot(DistancePlot):
    distance = "mu"
    filename = "distance_modulus"
    name = "Distance Modulus $\\mu$"

class CMBSpectrumPlot(Plot):
    "The four different C_ell plots are subclasses of this"
    def plot(self):
        super(CMBSpectrumPlot, self).plot()
        ell = self.load_file("cmb_cl", "ell")
        c_ell = self.load_file("cmb_cl", self.name)
        pylab.plot(ell, c_ell)
        pylab.grid()
        pylab.xlabel("$\\ell$")
        pylab.ylabel("$\\ell(\\ell+1) C_\\ell/2\\pi \\mathrm{"
                      + self.name.upper ()
                      + "} / uK^2$")

class TTPlot(CMBSpectrumPlot):
    name = filename = "tt"

class EEPlot(CMBSpectrumPlot):
    name = filename = "ee"

class TEPlot(CMBSpectrumPlot):
    name = filename = "te"

class BBPlot(CMBSpectrumPlot):
    name = filename = "bb"
    def plot(self):
        super(BBPlot,self).plot()
        pylab.xlim(0,400)



class GrandPlot(Plot):
    "Grand CMB plot with all four spectra"
    filename = "grand"
    def plot(self):
        super(GrandPlot, self).plot()
        ell = self.load_file("cmb_cl", "ell")
        for name in ['tt', 'ee', 'te', 'bb']:
            c_ell = self.load_file("cmb_cl", name)
            pylab.loglog(ell, abs(c_ell), label=name.upper())
        pylab.legend()
        pylab.grid()
        pylab.xlabel("$\\ell$")
        pylab.ylabel("$\\ell(\\ell+1) C_\\ell/2\\pi / uK^2$")



class MatterPowerPlot(Plot):
    "Matter power spectrum, maybe including non-linear plot too if available"
    filename = "matter_power"
    def plot_section(self, section, label, p_name='p_k'):
        kh = self.load_file(section, "k_h")
        z = self.load_file(section, "z")
        p = self.load_file(section, p_name)
        if (p<0).all(): p*=-1
        z = np.atleast_1d(z)
        kh = np.atleast_1d(kh)
        p = np.atleast_2d(p)
        nk = len(kh)
        nz = len(z)
        if p.shape==(nz,nk):
            p = p.T
        pylab.loglog(kh, p[:,0], label=label)

    def power_files_exist(self, name):
        exist = [os.path.exists(
                os.path.join(self.dirname, name, filename+".txt"))
            for filename in ["k_h", "z", "p_k"]]
        return all(exist)


    def plot(self):
        super(MatterPowerPlot, self).plot()
        done_any=False
        if self.power_files_exist("matter_power_lin"):
            self.plot_section("matter_power_lin", "Linear")
            done_any=True
        if self.power_files_exist("matter_power_nl"):
            self.plot_section("matter_power_nl", "Non-Linear")
            done_any=True
        if self.power_files_exist("matter_power_gal"):
            self.plot_section("matter_power_gal", "Galaxy")
            done_any=True
        if self.power_files_exist("matter_power_no_bao"):
            self.plot_section("matter_power_no_bao", "No BAO")
            done_any=True
        if self.power_files_exist("intrinsic_alignment_parameters"):
            self.plot_section("intrinsic_alignment_parameters", "Intrinsic-intrinsic", p_name='p_ii')
            done_any=True
        if self.power_files_exist("intrinsic_alignment_parameters"):
            self.plot_section("intrinsic_alignment_parameters", "Shear-intrinsic", p_name='p_gi')
            done_any=True
        if not done_any:
            raise IOError("Not making plot: %s (no data in this sample)"% self.__class__.__name__[:-4])
        pylab.xlabel("$k / (Mpc/h)$")
        pylab.ylabel("$P(k) / (h^1 Mpc)^3$")
        pylab.grid()
        pylab.legend()



class ShearSpectrumPlot(Plot):
    "Shear-shear power spectrum"
    filename = "shear_power"
    ylim = (1e-8,1e-3)
    def plot(self):
        super(ShearSpectrumPlot, self).plot()
        self.plot_section("shear_cl")
        if os.path.exists(self.dirname + "/shear_cl_gg"):
            self.plot_section("shear_cl_gg")
        if os.path.exists(self.dirname + "/shear_cl_gi"):
            self.plot_section("shear_cl_gi")
        if os.path.exists(self.dirname + "/shear_cl_ii"):
            self.plot_section("shear_cl_ii")

    def plot_section(self, section):
        nbin = 0
        for i in range(1,100):
            filename = self.file_path(section,
                              "bin_{0}_{0}".format (i))
            if os.path.exists(filename):
                nbin += 1
            else:
                break
        if nbin==0:
            IOError("No data for plot: %s"% self.__class__.__name__[:-4])

        ell = self.load_file(section, "ell")
        sz = 1.0/(nbin+2)
        for i in range(1, nbin+1):
            for j in range(1, i+1):
                rect = (i*sz,j*sz,sz,sz)
                self.figure.add_axes(rect)
                #pylab.ploy()
                #pylab.subplot(nbin, nbin, (nbin*nbin)-nbin*(j-1)+i)
                cl = self.load_file(section,
                                "bin_{0}_{1}".format(i,j))

                if all(cl<=0):
                    cl *= -1
                pylab.loglog(ell, ell*(ell+1.) * cl/2/np.pi)
                pylab.ylim(*self.ylim)
                if i==1 and j==1:
                    pylab.xlabel("$\\ell$")
                    pylab.ylabel("$\\ell (\\ell+1) C_\\ell / 2 \\pi$")
                else:
                    pylab.gca().xaxis.set_ticklabels([])
                    pylab.gca().yaxis.set_ticklabels([])
                pylab.gca().tick_params(length=0.0, which='minor')
                pylab.gca().tick_params(length=3.0, which='major')
                pylab.gca().tick_params(labelsize=10)

                if section=="shear_cl":
                    pylab.text(1.5*ell.min(),
                               1.8e-4,
                               "(%d,%d)"%(i,j),
                                fontsize=8,
                                 color='red')
                    pylab.grid()


class MatterPower2D(ShearSpectrumPlot):
    "2D Matter power spectrum"
    filename = "matter_power_2d"
    ylim = (1e-6,1.0)
    def plot(self):
        super(ShearSpectrumPlot, self).plot()
        self.plot_section("matter_cl")


class ShearCorrelationPlusPlot(Plot):
    "Shear-shear correlation xi plus"
    filename = "shear_xi_plus"
    def plot(self):
        super(ShearCorrelationPlusPlot, self).plot()
        nbin = 0
        for i in range(1,100):
            filename = self.file_path("shear_xi_plus",
                                      "bin_{0}_{0}".format(i))
            if os.path.exists(filename):
                nbin += 1
            else:
                break
        if nbin==0:
            IOError("No data for plot: %s"% self.__class__.__name__[:-4])

        theta = self.load_file("shear_xi_plus", "theta")
        sz = 1.0/(nbin+2)
        for i in range(1, nbin+1):
            for j in range(1, i+1):
                rect = (i*sz,j*sz,sz,sz)
                self.figure.add_axes(rect)
                #pylab.ploy()
                #pylab.subplot(nbin, nbin, (nbin*nbin)-nbin*(j-1)+i)
                xi = self.load_file("shear_xi_plus",
                                "bin_{0}_{1}".format(i,j))
                pylab.loglog(theta, xi)
                pylab.xlim(1e-4,1e-1)
                pylab.ylim(2e-7,1e-3)
                if i==1 and j==1:
                    pylab.xlabel("$\\theta$")
                    pylab.ylabel("$\\xi_+(\\theta)$")
                else:
                    pylab.gca().xaxis.set_ticklabels([])
                    pylab.gca().yaxis.set_ticklabels([])

                pylab.gca().tick_params(length=0.0, which='minor')
                pylab.gca().tick_params(length=3.0, which='major')
                pylab.gca().tick_params(labelsize=10)

                pylab.text(1.5e-3,1.8e-4, "(%d,%d)"%(i,j), fontsize=8,
                           color='red')

                pylab.grid()



class ShearCorrelationMinusPlot(Plot):
    "Shear-shear correlation xi minus"
    filename = "shear_xi_minus"
    def plot(self):
        super(ShearCorrelationMinusPlot, self).plot()
        nbin = 0
        for i in range(1,100):
            filename = self.file_path("shear_xi_minus",
                                      "bin_{0}_{0}".format(i))
            if os.path.exists(filename):
                nbin += 1
            else:
                break
        if nbin==0:
            IOError("No data for plot: %s"% self.__class__.__name__[:-4])

        theta = self.load_file("shear_xi_minus", "theta")
        sz = 1.0/(nbin+2)
        for i in range(1, nbin+1):
            for j in range(1, i+1):
                rect = (i*sz,j*sz,sz,sz)
                self.figure.add_axes(rect)
                #pylab.ploy()
                #pylab.subplot(nbin, nbin, (nbin*nbin)-nbin*(j-1)+i)
                xi = self.load_file("shear_xi_minus",
                                "bin_{0}_{1}".format(i,j))
                pylab.loglog(theta, xi)
                pylab.xlim(1e-4,1e-1)
                pylab.ylim(2e-7,1e-3)
                if i==1 and j==1:
                    pylab.xlabel("$\\theta$")
                    pylab.ylabel("$\\xi_+(\\theta)$")
                else:
                    pylab.gca().xaxis.set_ticklabels([])
                    pylab.gca().yaxis.set_ticklabels([])

                pylab.gca().tick_params(length=0.0, which='minor')
                pylab.gca().tick_params(length=3.0, which='major')
                pylab.gca().tick_params(labelsize=10)

                pylab.text(1.5e-3,1.8e-4, "(%d,%d)"%(i,j), fontsize=8,
                           color='red')

                pylab.grid()


class GrowthPlot(Plot):
    filename='growth'
    def plot(self):
        super(GrowthPlot,self).plot()
        section = "growth_parameters"
        z = self.load_file(section, "z")
        d_z = self.load_file(section, "d_z")
        f_z = self.load_file(section, "f_z")
        pylab.plot(z, d_z, label='$d(z)$')
        pylab.plot(z, f_z, label='$f(z)$')
        pylab.grid()
        pylab.xlabel("Redshift z")
        pylab.ylabel("Growth Functions")
        pylab.legend(loc='center right')


class LuminositySlopePlot(Plot):
    filename='galaxy_luminosity_slope'
    def plot(self):
        super(LuminositySlopePlot,self).plot()
        section = "galaxy_luminosity_function"
        z = self.load_file(section, "z")
        alpha = self.load_file(section, "alpha")
        pylab.plot(z, alpha)
        pylab.grid()
        pylab.xlabel("Redshift z")
        pylab.ylabel("Luminosity Function Slope $\\alpha$")



def main(args):
    utils.mkdir(args.output_dir)
    for cls in Plot.registry:
        try:
            cls.make(args.dirname, args.output_dir, args.prefix, args.type)
        except IOError as err:
            print(err)


if __name__ == '__main__':
    main (parser.parse_args ())
