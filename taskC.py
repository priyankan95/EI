#!/usr/bin/env python
# coding: utf-8

# In[18]:


import random
from mosaik.util import connect_randomly, connect_many_to_one
import mosaik
SIM_CONFIG = {
    'CSV':{
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'cmd': 'mosaik-hdf5 %(addr)s',
    },
    'VPPServer': {
        'python': 'simulators.VPPServer:VPPServer',
    },
    'HouseholdSim':{
        'python':'householdsim.mosaik:HouseholdSim',
    },
    'PVController':{
        'python': 'simulator.PVController:PVController',
    },
    'PyPower':{
        'python': 'mosaik_pypower.mosaik:PyPower',
    },
    'WebVis':{
        'cmd': 'mosaik-web -s 0.0.0.0:8000 %(addr)s',
    },
}
START = '24-01-01 00:00:00'
END = 24*3600 # 1 day
PV_DATA = 'data/pv_10kw.csv'
ENERGY_REQUIREMENTS_FILE = 'data/energy_requirements.csv'
PROFILE_FILE = 'data/profiles.data.gz'
GRID_NAME = 'demo_lv_grid'
GRID_FILE = 'data/%s.json'% GRID_NAME
PV_PEAK = 10000
NUMBER_OF_PV_PLANTS = 10
def main():
    random.seed(24)
    world = mosaik.World(SIM_CONFIG)
    create_scenario(world)
    world.run(until = END, rt_factor = 1/3600)
def create_scenario(world):
    # start simulators
    pypower = world.start('PyPower', step_size = 15*60)
    hhsim = world.start('HouseholdSim')
    pvsim = world.start('CSV', sim_start = START, datafile = PV_DATA)
    
    energy_market = world.start('CSV', sim_start = START, datafile = ENERGY_REQUIREMENTS_FILE)
    vpp_server = world.start('VPPServer')
    pvcontroller = world.start('PVController')
    
    # Instantiate models
    grid = pvcontroller.Grid(gridfile=GRID_FILE).children
    houses = hhsim.ResidentialLoads(sim_start = START, profile_file = PROFILE_FILE, grid_name = GRID_NAME).children
    pvs = pvsim.PV.create(20)
    market = energy_market.Market.create(20)
    vpps = vpp_server.VPPServer(p_peak=PV_PEAK)
    pvcs = pvcontroller.PVController.create(NUMBER_OF_PV_PLANTS)


    #connect entities
    connect_buildings_to_grid(world, house, grid)
    connect_randomly(world, pvs, [e for e in grid if 'node' in e.eid], 'P')
    
    connect_many_to_one(world, pvs, market, vpps, 'P')
    connect.world(world, vpps, pvcs, 'V')
    
    # Database
    db = world.start('DB', step_size=60, duration=END)
    hdf5 = db.Database(filename='demo.hdf5')
    connect_many_to_one(world, houses, hdf5, 'P_out')
    connect_many_to_one(world, pvs, hdf5, 'P')

    nodes = [e for e in grid if e.type in ('RefBus, PQBus')]
    connect_many_to_one(world, nodes, hdf5, 'P', 'Q', 'Vl', 'Vm', 'Va')

    branches = [e for e in grid if e.type in ('Transformer', 'Branch')]
    connect_many_to_one(world, branches, hdf5,
                        'P_from', 'Q_from', 'P_to', 'P_from')
    #web visualization
      webvis = world.start('WebVis', start_date=START, step_size=60)
    webvis.set_config(ignore_types=['Topology', 'ResidentialLoads', 'Grid',
                                    'Database'])
    vis_topo = webvis.Topology()

    connect_many_to_one(world, nodes, vis_topo, 'P', 'Vm')
    webvis.set_etypes({
        'RefBus': {
            'cls': 'refbus',
            'attr': 'P',
            'unit': 'P [W]',
            'default': 0,
            'min': 0,
            'max': 30000,
        },
        'PQBus': {
            'cls': 'pqbus',
            'attr': 'Vm',
            'unit': 'U [V]',
            'default': 230,
            'min': 0.99 * 230,
            'max': 1.01 * 230,
        },
    })

    connect_many_to_one(world, houses, vis_topo, 'P_out')
    webvis.set_etypes({
        'House': {
            'cls': 'load',
            'attr': 'P_out',
            'unit': 'P [W]',
            'default': 0,
            'min': 0,
            'max': 3000,
        },
    })

    connect_many_to_one(world, pvs, vis_topo, 'P')
    webvis.set_etypes({
        'PV': {
            'cls': 'gen',
            'attr': 'P',
            'unit': 'P [W]',
            'default': 0,
            'min': -10000,
            'max': 0,
        },
    })
    
    connect_many_to_one(world, pvs, vis_topo, )


def connect_buildings_to_grid(world, houses, grid):
    buses = filter(lambda e: e.type == 'PQBus', grid)
    buses = {b.eid.split('-')[1]: b for b in buses}
    house_data = world.get_data(houses, 'node_id')
    for house in houses:
        node_id = house_data[house]['node_id']
        world.connect(house, buses[node_id], ('P_out', 'P'))


if __name__ == '__main__':
    main()

    
    
    
    
    
    
    
                  
    
    
    


# In[9]:





# In[ ]:




