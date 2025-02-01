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

    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)
    print("Light id:", light_id)
    print("Current phase:", current_phase)

    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)

    """
    Phases: 
      (0) E & W = green, N & S = red
      (1) E & W = yellow, N & S = red, WITH left turns still active (to allow cars to leave intersection)
      (2) E & W LEFT TURNING LANES ONLY = green, everything else = red
      (3) E & W LEFT TURNING LANES ONLY = yellow, everything else = red
      (4) ALL RED
      (5) N & S = green (including left turn lanes), E & W = red
      (6) N & S LEFT TURNING LANES = green, N & S EVERYTHING ELSE = yellow, E & W = red (allows cars turning left to exit)
      (7) N & S LEFT TURNING LANES ONLY = green, N & S EVERYTHING ELSE = red, E & W = red
      (8) N & S LEFT TURNING LANES ONLY = yellow, N & S EVERYTHING ELSE = red, E & W = red
      (9) ALL RED
      note (4) and (9) are duplicate states

      Define action 0 as switching to green E & W ALL
      Define action 1 as switching to green E & W left turn advance
      Define action 2 as switching to green N & S left turn advance
      Define action 3 as switching to green N & S ALL

    """
    current_phase = 2
    action = 0
    if action == 0 and current_phase != 0:
        if current_phase == 2:
            traci.trafficlight.setPhase(light_id, 3)  # transition to yellow
        elif current_phase == 7:
            traci.trafficlight.setPhase(light_id,  8)
        elif current_phase == 5:
            traci.trafficLight.setPhase(light_id, 6)
            traci.trafficlight.setPhaseDuration(light_id, 3)
        for i in range(3):
            traci.simulationStep()
        traci.trafficlight.setPhase(light_id, 0)  # set E-W green
        traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
        for i in range(5):
            traci.simulationStep()# ensure light is green for at least 3 seconds
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