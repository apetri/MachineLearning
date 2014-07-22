####################################################
#######LensTools functionality######################
####################################################

from lenstools import ConvergenceMap,Ensemble,GaussianNoiseGenerator
from lenstools.index import PDF,Indexer
from lenstools.defaults import load_fits_default_convergence

#####################################################

import logging
import numpy as np

#########################################################################################
#########This function gets called on every map image and computes the histograms########
#########################################################################################

def compute_map_histograms(args):

	assert "map_id" in args.keys()
	assert "simulation_set" in args.keys()
	assert "smoothing_scales" in args.keys()
	assert "redshift" in args.keys()
	assert "index" in args.keys()
	assert "generator" in args.keys()
	assert "bin_edges" in args.keys()

	assert len(args["index"].descriptor_list) == len(args["smoothing_scales"])

	z = args["redshift"]

	#Get map name to analyze
	map_name = args["simulation_set"].getNames(z=z,realizations=[args["map_id"]])[0]

	#Load the convergence map
	convergence_map = ConvergenceMap.fromfilename(map_name,loader=load_fits_default_convergence)

	#Generate the shape noise map
	noise_map = args["generator"].getShapeNoise(z=z,ngal=15.0,seed=args["map_id"])

	#Add the noise
	convergence_map += noise_map

	#Measure the features
	hist_output = np.zeros(args["index"].size)
	for n,descriptor in enumerate(args["index"].descriptor_list):

		logging.debug("Processing {0} x {1} arcmin".format(map_name,args["smoothing_scales"][n]))

		smoothed_map = convergence_map.smooth(args["smoothing_scales"][n])
		v,hist_output[descriptor.first:descriptor.last] = smoothed_map.pdf(args["bin_edges"])

	#Return the histograms in array format
	return hist_output

def measure_all_histograms(models,options,pool):

	ensemble_list = list()

	#Look at a sample map
	sample_map = ConvergenceMap.fromfilename(models[0].getNames(z=1.0,realizations=[1])[0],loader=load_fits_default_convergence)
	#Initialize Gaussian shape noise generator for the sample map shape and angle
	generator = GaussianNoiseGenerator.forMap(sample_map)

	#Parsed from options
	num_realizations = options.getint("analysis","num_realizations")
	smoothing_scales = [float(scale) for scale in options.get("analysis","smoothing_scales").split(",")]
	######DANGER!!!############
	bin_edges = eval(options.get("analysis","bin_edges"))
	bin_midpoints = 0.5*(bin_edges[1:] + bin_edges[:-1])
	###########################
	z = options.getfloat("analysis","redshift")

	#Create smoothing scale index for the histogram
	idx = Indexer.stack([PDF(bin_edges) for scale in smoothing_scales])

	#Build Ensemble instance with the maps to analyze
	map_ensemble = Ensemble.fromfilelist(range(1,num_realizations+1))
	
	#The for loop runs the distributed computations
	for model in models:
		
		#Measure the histograms and load the data in the ensemble
		map_ensemble.load(callback_loader=compute_map_histograms,pool=pool,simulation_set=model,smoothing_scales=smoothing_scales,index=idx,generator=generator,bin_edges=bin_edges,redshift=z)

		#Append to output
		ensemble_list.append(map_ensemble)

	return bin_midpoints,idx,ensemble_list