import scipy as sp
import matplotlib.pyplot as plt

""" Some useful formulae:

-Beam propagation:
Rayleigh range = pi * w_0**2 / lambda
Radius of the beam w(z)= w_0 * sqrt(1+ (z/zR)**2)

-Beam transformation (for thin lenses):
--Location and size of the beam waist in the output
denom=((d_in/f-1)**2 +(zR/f)**2)
d_out= f * (1+ (d_in/f -1)/denom)
w_0out= w_0in/sqrt(denom)

--Magnification:   M= w_0out/w_0in = 1/sqrt(denom)
--Maximum magnification: f/z_c
--Size at the focus: w(d_out==f)= f*w_0in/zR_in     (only the waist if d_in=f)

-Gaussian Beam telescope:
Pair of focusing elements separated by ther focal distances

w_0out= w_0in * f2/f1    (wavelength independent)

d_out= f2/f2 *(f1+f2-d_in* f2/f1) """



import scipy as sp
import matplotlib.pyplot as plt


def RayleighR(self):
    return sp.pi*self.w0**2/self.lambd


class BeamSection:
    """ Section of the beam characterized by a waist, a wavelength and the position of the waist.
    It contains all the information to represent a Gaussian beam that propagates in free space.

    The function "transformByLens" returns another object of this same type that is the
    transformation of the beam section by a lens.

    """

    def __init__(self, wavelength, waist,position):
        """ Initialize the values of position, waist and wavelength.
        It also creates the Rayleigh range zR

        """
        self.z0 = position
        self.w0 = waist
        self.lambd = wavelength
        self.zR = sp.pi * waist**2 / wavelength

    def waist(self, z):
        """ Outputs the waist of the gaussian beam at a position z.  The position can be an array """
        return self.w0* sp.sqrt(1 + (z-self.z0)**2 /self.zR**2)

    def divergence(self):
        """ Calculates the divergence of the beam.  The full angular spread is twice this number """
        return self.lambd/(sp.pi * self.w0)

    def transformByLens(self, f, z):
        """ Transforms the Gaussian beam to one "after" the lens with focal f placed at z"""
        d_in = z - self.z0
        #denom is the common denominator of the changes in z0 and w0
        denom = (d_in/f-1)**2 + (self.zR/f)**2
        d_out = f * (1+(d_in/f - 1) / denom)
        #Change the parameters of the Gaussian
        z0 = z + d_out
        w0 = self.w0/sp.sqrt(denom)
        return BeamSection(self.lambd,w0,z0)
    
    def report(self):
        """ Print some parameters"""
        print "##############################"
        print "Waist= {0:e}".format(self.w0)
        print "Position= {0:e}".format(self.z0)
        print "Rayleigh Range = {0:e}".format(self.zR)
        print "##############################"

    def parameters(self):
        return (self.lambd, self.w0, self.z0)

class BeamPropagation():
    """ Collection of Gaussian beams with lenses. """

    ####################
    #  Definition
    ####################
    
    def __init__(self,originalBeamParams,lenses):
        """ Creates a collection of beam+lenses to be used by the object.

        -OriginalBeamParams is a vector that we can pass a BeamSection object as
        BeamSection(*OriginalBeamParams) to create the initial beam.

        -lenses is a matrix of (2xN) elements where the second index cycles through
        the elements, lenses[1,:] are the positions and lenses[0,:] are the focals.

        """
        # In future implementations, "lenses" can be "transformations", as a collection
        # of objects with certain parameters that are passed to the initial beam to create
        # different sections. The BeamSection, therefore, should admit a method __transform__
        # that takes one of these objects and creates another BeamSection object.
        distancesList=lenses[1,:]
        focalsList=lenses[0,:]
        
        #The parameters of the lenses are stored and sorted according to the distances
        self.lensPositions = distancesList[distancesList.argsort()]
        self.lensFocals = focalsList[distancesList.argsort()]
        self.z0 = originalBeamParams[2]
        self.w0 = originalBeamParams[1]
        self.amountElements = len(self.lensPositions)
        self.amountSections = self.amountElements + 1

        #Obtain the intervals of application for each of the beam sections
        beamsLimits= sp.zeros((2,self.amountSections))
        beamsLimits[0,0]=-sp.inf
        beamsLimits[0,1:]=self.lensPositions
        beamsLimits[1,:-1]=self.lensPositions
        beamsLimits[1,-1]=sp.inf
        self.beamsLimits = beamsLimits

        #CHANGE: make sure that the waist is between lenses. Now, only make sure that the
        #position of the waist is smaller than the rest
        if self.z0 > self.lensPositions.all():
            raise Exception('The position of the initial waist is not smaller than the positions of the lenses')
        else:
            #Create a list of beam parameters
            beamParams=sp.zeros((3,self.amountSections))
            beamParams[:,0]=originalBeamParams
            parms=originalBeamParams
            for ii in range(0,self.amountElements):
                oldBeam=BeamSection(*parms)
                newBeam=oldBeam.transformByLens(self.lensFocals[ii], self.lensPositions[ii])
                beamParams[:,ii+1]=newBeam.parameters()
                parms=beamParams[:,ii+1]
                oldBeam=newBeam
            self.beamParams=beamParams
                
    def waist(self,z):
        """ Obtain the waist of the beam at a point z.
        Not suitable for arrays

        """
        #The beamsLimits is a matrix with the upper and lower limits
        #of the intervales for each section. If we compare the matrix
        #to the z value we are interested in and sum them, only the
        #right section will obtain a "1" (the value will only be greater
        #than the lower limit)
        index=sp.arange(0,self.amountSections)[sum(z>=self.beamsLimits)==1]
        #Then, we obtain the waist from the appropriate BeamSection
        return BeamSection(*self.beamParams[:,index]).waist(z)
        

    ####################
    # Report methods
    ####################

    def reportLenses(self):
        """ Shows an annotated table with the positions and focals of the lenses
        """
        print " Position    Focal   "
        print "---------------------"
        for ii in range(self.amountElements):
            print "{0:10.2e} {1:10.2e}".format(self.lensPositions[ii], self.lensFocals[ii])
        print "====================="
    def reportParameters(self):
        """ Shows an annotated table with the parameters of the different sections of beam
        between the lenses.

        """
        print " Lambd         w0         z0   "
        print "-------------------------------"
        for ii in range(self.amountSections):
            print "{0:10.2e} {1:10.2e} {2:10.2e}".format(self.beamParams[0,ii], self.beamParams[1,ii], self.beamParams[2,ii])
        print "====================="

        
    ####################
    # Plotting methods
    ####################

    def plotFull(self,zmin=None,zmax=None,**kwargs):
        """ Plots the Gaussian beam width within the object from zmin to zmax.

        If not defined, zmin will be the position of the initial waist and
        zmax will be the position of the focus of the last lens.

        kwargs:
        sym [True|False]  - Plots the mirror image of the width profile alongside the normal one.
        new [True|False]  - Whether it plots using a new figure
        axes [ axes object] - plots the figure using the command axes.plot ()

        """
        NUMBER_OF_STEPS=300
        #xmax=(self.lensPositions[-1] + self.lensFocals[-1])
        #xmin=self.z0
        if (zmin is None) | (zmax is None):
            zmin=self.z0
            zmax= self.lensPositions[-1] + self.lensFocals[-1]
            

        z=sp.arange(zmin,zmax,(zmax-zmin)/NUMBER_OF_STEPS)
        beamWidth=sp.zeros(len(z))
        if ('new' in kwargs):
            if kwargs['new']== True:
                plt.figure()
        
        
        #This time, opposite to the waist method, it will loop over the different
        #sections, checking which parts of the beam fall under the limits of each
        #section. Then, it will use the "waist" method in the BeamSection object
        #to plot the beam width.
        for ii in range(self.amountSections):
            localIndices=((z>self.beamsLimits[0,ii]) &(z<=self.beamsLimits[1,ii]))
            zlocal= z[localIndices]
            if zlocal is not None:
                beamWidth[localIndices]=BeamSection(*self.beamParams[:,ii]).waist(zlocal)
        
        plt.plot(z,beamWidth,'r',linewidth=3)
        if ('sym' in kwargs):
            if kwargs['sym']== True:
                plt.plot(z,-beamWidth,'r',linewidth=3)
        

        #Add some labels (important, scientists!)
        plt.xlabel('z (m)')
        plt.ylabel('Width (m)')
        
        for ii in range(self.amountElements):
            plt.axvline(x=self.lensPositions[ii])
        plt.xlim(zmin,zmax)

            


    
##############################
# Some functions
##############################


def denominator(d_in,f,zR):
    return (d_in/f -1)**2 +(zR/f)**2

def propagated_waist(w_0,z,zR,sz):
    return w_0*sp.sqrt(1+((z-sz)/zR)**2)

def rayleigh_range(waist,lambd):
    return sp.pi*waist**2/lambd



