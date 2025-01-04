import traci
import sumolib
import time
import os
import subprocess

'''
Run this file to have the simulation automatically run. 

Notice that I am using sumo instead of sumo-gui in the for sumo binary
This allows us to perform multiple iterations on the same network which will be essential for training
It also runs through the program much faster since it doesn't need to handle any rendering
This will be another benefit for the training time!

'''


# SUMO binary (either sumo-gui or sumo depending on whether you want to see the GUI or not)
sumo_binary = sumolib.checkBinary('sumo-gui')  # Use 'sumo-gui' if you want to see the GUI

# Path to your SUMO configuration file (.sumocfg)
sumo_config = os.path.join(os.path.dirname(__file__), './network/mcmaster.sumocfg')


# Define TraCI setup
def run_sumo():
    # Start the SUMO simulation using TraCI
    traci.start([sumo_binary, "--start", "-c", sumo_config, "--no-step-log"])

    # Simulation loop
    step = 0
    try:
        while step < 190:  # Running this for 200 steps, but you can make it run indefinitely
            
            traci.simulationStep()  # Advance the simulation by one step
            step += 1


    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:

        traci.load(["-c", sumo_config])
        print("Finished reloading")
        print("finished close")


    traci.close()

if __name__ == "__main__":
    run_sumo()