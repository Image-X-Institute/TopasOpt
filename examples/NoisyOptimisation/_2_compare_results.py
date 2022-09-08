from pathlib import Path
from TopasOpt.utilities import get_all_files

# update this to wherever your data from part 1 is stored:
data_dir = Path(r'/home/brendan/RDS/PRJ-Phaser/PhaserSims/topas/noise_sims')
sims_to_investigate = ['n_particles_20000', 'n_particles_40000',  'n_particles_50000']

for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    get_all_files(data_loc, 'bin')

