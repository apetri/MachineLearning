import sys,ConfigParser

options = ConfigParser.ConfigParser()

options.add_section("simulations") 
options.set("simulations","root_path","/Users/andreapetri/Documents/Columbia/spurious_shear/convergence_maps")

options.add_section("analysis") 
	
options.set("analysis","num_realizations","3")
options.set("analysis","smoothing_scales","0.1,0.5,1.0")
options.set("analysis","bin_edges","np.ogrid[-0.15:0.15:15j]")
options.set("analysis","redshift","1.0")


with open(sys.argv[1],"w") as configfile:
	options.write(configfile)