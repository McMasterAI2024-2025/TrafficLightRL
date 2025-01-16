import traci
import sumolib
import time
import os
import subprocess



sumo_binary = sumolib.checkBinary('sumo-gui')  # Use 'sumo-gui' if you want to see the GUI

# Path to your SUMO configuration file (.sumocfg)
sumo_config = os.path.join(os.path.dirname(__file__), './network/queens.sumocfg')



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