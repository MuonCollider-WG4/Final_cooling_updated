import multiprocessing
from skopt import gp_minimize
import os
import shutil
import numpy as np
import subprocess
from billiard import Pool
import multiprocessing
from skopt import Optimizer
from skopt.space import Real
from scipy.optimize import differential_evolution,NonlinearConstraint
from functools import partial

ncells = 1
region = 2
cells_list = [1, region]
pre = '/home/zhurh/final_cooling_lower_field_rf_stage2/stage3/'
beam_filename = 'beam_final_cooling_stage3.beam'
g4bl_filename = 'final_cooling_stage3.g4bl'
event_id = []
with open(pre + beam_filename, 'r') as f:
    out = f.readlines()
events_num = len(out) - 3
cores_num = 16
temp = [1]
for i in range(cores_num):
    if i != cores_num-1:
        temp.append(temp[i] + int(events_num/cores_num))
    else:
        temp.append(events_num)
cores_events = []
for i in range(cores_num):
    cores_events.append([temp[i],temp[i+1]-1])

def run_g4bl(present_dir, events):
    new_loc = present_dir + 'events' + str(events[0])
    os.makedirs(new_loc)
    shutil.copy(present_dir + beam_filename, new_loc)
    shutil.copy(present_dir + g4bl_filename, new_loc)
    os.chdir(new_loc)
    g4bl_cmd = subprocess.Popen('g4bl '+ g4bl_filename + ' first=' + str(events[0]) + ' last=' + str(events[1]) + ' > print.out',cwd='./',shell=True)
    g4bl_cmd.wait()

def find_index(dire):
    index_start_list = []
    index_end_list = []
    with open(dire + 'particles_info.txt', 'r') as f:
        out = f.readlines()
    #for i in range(1,ncells+2):
    for i in cells_list:
        flag1 = 0
        flag2 = 0
        if i!=ncells+1:
            for j in range(4,len(out)):
                if int(out[j-1].strip().split()[0])==0 and int(out[j].strip().split()[4])==i:
                    index_start_list.append(j)
                    flag1 = 1
                if int(out[j].strip().split()[4])==i and int(out[j+1].strip().split()[0])==0:
                    index_end_list.append(j)
                    flag2 = 1
                if flag1==1 and flag2==1:
                    break
        else:
            for j in range(4,len(out)):
                if int(out[j-1].strip().split()[0])==0 and int(out[j].strip().split()[4])==i:
                    index_start_list.append(j)
            index_end_list.append(len(out)-1)
    return index_start_list, index_end_list

def check_regn(path):
    flag1 = 0
    with open(path + 'particles_info.txt', 'r') as f:
        out = f.readlines()
    regn_index = []
    for i in range(3,len(out)):
        regn_index.append(int(out[i].strip().split()[4]))
    if len(regn_index)>0:
        if max(regn_index)==ncells + 1:
            flag1 = 1
    flag2 = 1
    with open(path + 'print.out', 'r') as f:
        out = f.readlines()
    for i in range(len(out)):
        if 'G4Exception: No reference' in out[i]:
            flag2 = 0
    return flag1*flag2



def run(present_dir):
    pool = Pool(cores_num)
    pool.map(partial(run_g4bl,present_dir), cores_events)
    pool.close()
    pool.join()
    #process_list = list()
    
    #for i in range(cores_num):
    #    process_list.append(multiprocessing.Process(target=run_g4bl, args=(present_dir,cores_events[i])))
        
    #for process in process_list:
    #    process.start()
    #for process in process_list:
    #    process.join()
    content = ['#NTuple/Z0 \n', '#Units are ns, meters, GeV/c, Tesla, and V/m \n', '#IEVT IPNUM IPTYP IPFLG JSRG T X Y Z Px Py Pz Bx By Bz Weight Ex Ey Ez SARC POLx POLy POLz \n']
    pre_list = [present_dir + 'events' + str(cores_events[i][0]) + '/' for i in range(cores_num)]
    index_start_list_all = []
    index_end_list_all = []
    flag = 1
    for i in range(len(pre_list)):
        temp = check_regn(pre_list[i])
        flag = flag*temp
    if flag==1:
        for dire in pre_list:
            index_start_list, index_end_list = find_index(dire)
            index_start_list_all.append(index_start_list)
            index_end_list_all.append(index_end_list)
        #for i in range(ncells+1):
        for i in range(len(cells_list)):
            for j in range(len(pre_list)):
                with open(pre_list[j] + 'particles_info.txt', 'r') as f:
                    out = f.readlines()
                if j==0:
                    for k in range(index_start_list_all[j][i]-1, index_end_list_all[j][i]+1):
                        content.append(out[k])
                else:
                    for k in range(index_start_list_all[j][i], index_end_list_all[j][i]+1):
                        content.append(out[k])
        if os.path.exists(present_dir + 'for009.dat'):
            os.remove(present_dir + 'for009.dat')
        with open(present_dir + 'for009.dat', 'w+') as f:
            f.writelines(content)
        os.chdir(pre)
        for dire in pre_list:
            shutil.rmtree(dire)
        cmd = subprocess.Popen('ecalc9f > out.txt', cwd=present_dir, shell=True)
        cmd.wait()
        os.remove(present_dir + beam_filename)
        os.remove(present_dir + 'for009.dat')
        with open(present_dir + 'ecalc9f.dat', 'r') as f:
            out = f.readlines()
        emit_t_start = float(out[13].strip().split()[3])
        emit_l_start = float(out[13].strip().split()[4])
        emit_6d_start = float(out[13].strip().split()[5])
        particles_num_start = float(out[13].strip().split()[12])
        #emit_t_regn = float(out[14+region].strip().split()[3])
        #emit_l_regn = float(out[14+region].strip().split()[4])
        #particles_num_regn = float(out[14+region].strip().split()[12])
        #emit_6d_regn = float(out[14+region].strip().split()[5])
        #pz_regn = float(out[14+region].strip().split()[7])
        emit_t_regn = float(out[-1].strip().split()[3])
        emit_l_regn = float(out[-1].strip().split()[4])
        particles_num_regn = float(out[-1].strip().split()[12])
        emit_6d_regn = float(out[-1].strip().split()[5])
        pz_regn = float(out[-1].strip().split()[7])
        sigma_energy_regn = float(out[-1].strip().split()[16])
        alpha_t_regn = float(out[-1].strip().split()[9])
        sigma_t_regn = float(out[-1].strip().split()[17])
        with open(pre + 'select_finer.txt', 'a+') as f:
            target = emit_t_regn/emit_t_start + 0.75*particles_num_start/particles_num_regn + 0.25*emit_l_regn/emit_l_start #+ np.abs(alpha_t_regn)
            f.write(str(target) + '\t' + str(emit_t_regn) + '\t' + str(emit_l_regn) + '\t' + str(emit_6d_regn) + '\t' + str(pz_regn) + '\t' + str(particles_num_regn) + '\t' + str(sigma_energy_regn) + '\t' + str(alpha_t_regn) + '\t' + str(sigma_t_regn) + '\t' + present_dir + '\n')
        return target
    else:
        os.chdir(pre)
        
        shutil.rmtree(present_dir)
        return np.random.uniform(1000,2000)

def score_func(x):
    init_dir = pre + 'files/'
    present_dir = init_dir + ','.join([str(round(i, 4)) for i in x]) + '/'
    if os.path.exists(present_dir):
        #print('file exsits')
        present_dir = pre + ','.join([str(i+np.random.uniform(0,1)) for i in x]) + '/'
    try:
        os.makedirs(present_dir)
    except:
        return np.random.uniform(100,200)
    shutil.copy(pre + beam_filename, present_dir)
    shutil.copy(pre + g4bl_filename, present_dir)
    shutil.copy(pre + 'ecalc9f', present_dir)
    shutil.copy(pre + 'ecalc9f.inp', present_dir)
    with open(present_dir + g4bl_filename, 'r') as f:
        out = f.readlines()
    parameters = ['current_M3', 'length_M3', 'current_drift', 'rf_fre','rf_grad_acc', 'rf_ph_acc', 'num_acc_rf', 
                   'next_current_M1', 'next_length_M1', 'next_current_HF', 'next_length_HF', 'next_absorber_length', 'next_current_M2', 'next_length_M2']
    for i in range(len(parameters)):
        if i==6:
            for j in range(len(out)):
                if parameters[i] in out[j]:
                    elements = out[j].strip().split('=')
                    elements[-1] = str(round(x[i]))
                    out[j] = '='.join(elements) + '\n'
                    break
        else:
            for j in range(len(out)):
                if parameters[i] in out[j]:
                    elements = out[j].strip().split('=')
                    elements[-1] = str(x[i])
                    out[j] = '='.join(elements) + '\n'
                    break
    os.remove(present_dir + g4bl_filename)
    with open(present_dir + g4bl_filename, 'w') as f:
        f.writelines(out)
    with open(present_dir + 'ecalc9f.inp', 'r') as f:
        out = f.readlines()
    out[5] = str(x[3]*1000) + '\n'
    os.remove(present_dir + 'ecalc9f.inp')
    with open(present_dir + 'ecalc9f.inp', 'w') as f:
        f.writelines(out)
    score = run(present_dir)
    #q.put(score)
    return score
    
def rf_constraint(x):
    return 15.5*np.power(x[3]/0.201, 0.75)-x[4] #1.88*np.sqrt(x[3]*10**9)/1000-x[4]

if __name__ == '__main__':
    #res = gp_minimize(score_func,[(-2.0,2.0),(100.0,150.0),(-4.0,4.0)], acq_func='gp_hedge',n_calls=150,n_initial_points=10, initial_point_generator='lhs')
    #optimizer = Optimizer(dimensions=[Real(-2.0,2.0),Real(100.0,150.0),Real(-4.0,0.0)], random_state=1, base_estimator='gp', initial_point_generator='lhs')
    #for i in range(100):
    #    print('now turn '+str(i+1))
    #    y = []
        
    #    x = optimizer.ask(n_points=10)
    #    process_list = list()
    #    q = multiprocessing.Queue()
    #    for i in range(10):
    #        process_list.append(multiprocessing.Process(target=score_func, args=(x[i],q), daemon=False))
    
    #    for process in process_list:
    #        process.start()
    #    for process in process_list:
    #        process.join()
    #    for process in process_list:
    #        y.append(q.get())
    #    optimizer.tell(x,y)
    nlc = NonlinearConstraint(rf_constraint, 0, +np.inf)
    bounds = [(-100, -10), (100, 1000), (10, 100), (0.015, 0.04), (1, 4.5), (15, 70), (2, 6), 
              (-250, -10), (100, 1500), (-600, -400), (500, 1000), (15, 40), (-250, -10), (500, 1000)]
    result = differential_evolution(score_func, bounds=bounds, constraints=(nlc,), popsize=70, polish=False, workers=10, maxiter=250, disp=True)