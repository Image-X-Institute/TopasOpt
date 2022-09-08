from GenerateTopasScripts import GenerateTopasScripts
import os
from pathlib import Path
import stat

def generate_run_all_scripts_shell_script(script_location, sims_to_run, topas_location='~/topas37', G4_DATA='~/G4Data'):
    FileName = script_location / 'RunAllFiles.sh'
    f = open(FileName, 'w+')
    f.write('# !/bin/bash\n\n')
    f.write('# This script sets up the topas environment then runs all listed files\n\n')
    f.write('# ensure that any errors cause the script to stop executing:\n')
    f.write('set - e\n\n')
    f.write(f'export TOPAS_G4_DATA_DIR={G4_DATA}\n')

    # add in all topas scripts which need to be run:
    for sim in sims_to_run:
        f.write('echo "Beginning analysis of: ' + sim.name + '"')
        f.write('\n')
        f.write(f'(time {topas_location}/bin/topas {sim.name}) &> ../logs/{sim.name}')
        f.write('\n')
    f.write('\necho "All done!"\n')
    # change file modifications:
    st = os.stat(FileName)
    os.chmod(FileName, st.st_mode | stat.S_IEXEC)
    f.close()

basedirectory = Path(os.path.expanduser('~')) / 'Documents' / 'temp' / 'noise_sims'
if not basedirectory.is_dir():
    basedirectory.mkdir()

n_sims_to_generate = range(10)
n_particles_to_investigate = [50000, 40000, 20000]

variable_dict = {'UpStreamApertureRadius': 1.8,
                 'DownStreamApertureRadius': 2.5,
                 'CollimatorThickness': 27,
                 'n_primaries': 50000}

for n_particles in n_particles_to_investigate:
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


