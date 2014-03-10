#!/usr/bin/python

import sys
import numpy as np
from .ComponentBase import Component

def runningMeanFast(x, N):
	'''
	x = array of points
	N = window width
	Ref: http://stackoverflow.com/questions/13728392/moving-average-or-running-mean
	'''
	return np.convolve(x, np.ones((N,))/N)[(N-1):]

class NuclearContinuumComponent(Component):
	'''
	AGN Continuum Component
	\f$ F_{\lambda,{\rm PL}}=F_{\rm PL,0} \ \left(\frac{\lambda}{\lambda_0}\right)^{\alpha} \f$ 
	This component has two parameters:
	
	normalization : \f$ F_{\rm PL,0} \f$ 
	slope : \f$ \alpha \f$ 
	
	'''
	def __init__(self):
		super(NuclearContinuumComponent, self).__init__()

		self.model_parameter_names = list()
		self.model_parameter_names.append("normalization")
		self.model_parameter_names.append("slope")
		
		self._norm_wavelength =  None
		
		self.normalization_min = None
		self.normalization_max = None
		self.slope_min = None
		self.slope_max = None
		
	@property
	def is_analytic(self):
		return True	
	
	def initial_values(self, spectrum=None):
		'''
		Needs to sample from prior distribution.
		Return type must be a list (not an np.array).
		
		Called by the emcee.
		'''
				
		boxcar_width = 5 # width of smoothing function
		
		self.flux_min = 0
		self.flux_max = max(runningMeanFast(spectrum.flux, boxcar_width))
		
		normalization_init = np.random.uniform(low=self.flux_min,high=self.flux_max)

		self.slope_min = -3.0
		self.slope_max = 3.0

		slope_init = np.random.uniform(low=self.slope_min,high=self.slope_max)

		return [normalization_init, slope_init]


	def normalization_wavelength(self, data_spectrum_wavelength=None):
		'''
		
		'''
		if self._norm_wavelength is None:
			if data_spectrum_wavelength is None:
				raise Exception("The wavelength array of the data spectrum must be specified.")
			self._norm_wavelength = np.median(data_spectrum_wavelength)
		return self._norm_wavelength

	def ln_priors(self, params):
		'''
		Return a list of the ln of all of the priors.
		
		normalization : uniform linear prior between 0 and the maximum of the spectral flux after computing running median
		slope : uniform linear prior in range [-3,3]
		'''
		
		# need to return parameters as a list in the correct order
		ln_priors = list()
		
		normalization = params[self.parameter_index("normalization")]
		slope = params[self.parameter_index("slope")]
		
		if self.normalization_min < normalization < self.normalization_max:
			ln_priors.append(np.log(1))
		else:
			#arbitrarily small number
			ln_priors.append(-1.e17)
			
		if self.slope_min < slope < self.slope_max:
			ln_priors.append(np.log(1))
		else:
			#arbitrarily small number
			ln_priors.append(-1.e17)
			# TODO - suppress "RuntimeWarning: divide by zero encountered in log" warning.
			
		return ln_priors
		
	def flux(self, spectrum=None, parameters=None):
		'''
		Returns the flux for this component for a given wavelength grid
		and parameters. Will use the initial parameters if none are specified.
		'''
		assert len(parameters) == len(self.model_parameter_names), "The wrong number of indices were provided: {0}".format(parameters)
		
		# calculate flux of the component
		normalized_wavelengths = spectrum.wavelengths / \
			self.normalization_wavelength(data_spectrum_wavelength=spectrum.wavelengths)
		flux = parameters[0] * np.power(normalized_wavelengths, parameters[1])
		
		return flux
