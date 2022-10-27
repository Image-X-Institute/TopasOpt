from GenerateTopasScripts import GenerateTopasScripts
import os
from pathlib import Path
from TopasOpt.utilities import generate_run_all_scripts_shell_script
import json


basedirectory = Path(os.path.expanduser('~')) / 'Documents' / 'temp' / 'noise_sims'
if not basedirectory.is_dir():
    basedirectory.mkdir()

n_sims_to_generate = range(10)
n_particles_to_investigate = [10000, 30000]

variable_dict = {'UpStreamApertureRadius': 1.82,
                 'DownStreamApertureRadius': 2.5,
                 'CollimatorThickness': 27}

for n_particles in n_particles_to_investigate:
    particle_data = {}
    particle_data['n_particles'] = n_particles
    with open('particle_data.json', 'w') as fp:
        json.dump(particle_data, fp)  # GenerateTopasScripts will read this
    sim_directory = basedirectory / f'n_particles_{n_particles}'
    if not sim_directory.is_dir():
        sim_directory.mkdir()
    if not (sim_directory / 'Results').is_dir():
        (sim_directory / 'Results').mkdir()
    if not (sim_directory / 'logs').is_dir():
        (sim_directory / 'logs').mkdir()
    if not (sim_directory / 'scripts').is_dir():
        (sim_directory / 'scripts').mkdir()
    sim_num = 0
    variable_dict['n_primaries'] = n_particles
    ScriptsToRun = []
    for n_sim in n_sims_to_generate:
        [SimpleCollimator, WaterTank], [sim1_name, sim2_name] = GenerateTopasScripts('gah', n_sim, **variable_dict)
        sim_num += 1
        sim1 = sim_directory / 'scripts' / (sim1_name + '_' + str(sim_num) + '.tps')
        sim2 = sim_directory / 'scripts' / (sim2_name + '_' + str(sim_num) + '.tps')
        ScriptsToRun.append(sim1)
        ScriptsToRun.append(sim2)
        # write the first simulation
        f = open(sim1, 'w')
        for line in SimpleCollimator:
            f.write(line)
            f.write('\n')
        # write the second simulation
        f = open(sim2, 'w')
        for line in WaterTank:
            f.write(line)
            f.write('\n')
    # once all sims are generated, write a 'RunAllFiles.sh' script:
    generate_run_all_scripts_shell_script((sim_directory / 'scripts'), ScriptsToRun)


