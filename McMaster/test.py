import traci
import sumolib
import time
import os
import subprocess
import random

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

    lanes = {
      # Edge 1 (East incoming)
      "334693613#0_0": {"type": [0, 1, 0]},  # Stright lane
      "334693613#0_1": {"type": [0, 1, 0]},  # Straight lane
      "334693613#0_2": {"type": [0, 1, 0]},  # Straight lane
      "334693613#0_3": {"type": [1, 0, 0]},  # Left-turn lane

      # Edge 2 (West incoming)
      "150872238#1_4": {"type": [1, 0, 0]},  # Left-turn lane
      "150872238#1_3": {"type": [0, 1, 0]},  # Straight lane
      "150872238#1_2": {"type": [0, 1, 0]},  # Straight lane
      "150872238#1_1": {"type": [0, 1, 0]},  # Straight lane
      "150872238#1_0": {"type": [0, 0, 1]},  # Right-turn lane

      # Edge 3 (South incoming)
      "864501901#3_0": {"type": [1, 1, 1]},  # Left-Right-Straight-turn lane

      # Edge 4 (North incoming)
      "194417404#0_2": {"type": [1, 0, 0]},  # Left-turn lane
      "194417404#0_1": {"type": [0, 1, 0]},  # Straight lane
      "194417404#0_0": {"type": [0, 0, 1]}  # Right-turn lane
    }

    print("Keys:")
    print(lanes.keys())
    print()

    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)
    print("Light id:", light_id)
    print("Current phase:", current_phase)

    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)

    print("******** LANES &&&&&&&&&&&&&&&&")
    print(traci.lane.getIDList())
    print("###### END LANES ################\n\n\n\n\n\n\n")

    # Simulation loop

    edge_mapping = {
        "183330267": ["401622262", "156268074", "-864501901#0"], # East starting -> [right, stright, left]
        "150872238#0": ["-864501901#0", "262794389#4", "401622262"], # West starting -> [right, straight, left]
        "864501901#0": ["262794389#4", "401622262", "156268074"], # South starting -> [right, straight, left]
        "401622246#0": ["156268074", "-864501901#0", "262794389#4"] # North starting -> [left, straight, right]
    }


    for j in range(2):
        for i in range(5):
            vehicle_id = f"rand_car_{i}"

            start_edge = random.choice(list(edge_mapping.keys()))
            end_edge = random.choice(edge_mapping[start_edge])

            route_id = f"route_{vehicle_id}"

            try:
                traci.route.add(routeID=route_id, edges=[start_edge, end_edge])

                # Add the vehicle to the simulation
                traci.vehicle.add(vehID=vehicle_id, routeID=route_id)

                print(f"Deployed random vehicle {vehicle_id} from {start_edge} to {end_edge}")

                # Set a random speed for the vehicle
                traci.vehicle.setSpeed(vehicle_id, random.uniform(5, 15))

            except traci.TraCIException as e:
                pass
                #print(f"Failed to add vehicle {vehicle_id} on route from {start_edge} to {end_edge}: {e}")
        step = 0
        try:
            while step < 100:  # Running this for 200 steps, but you can make it run indefinitely

                lane_wait_times = [
                    traci.lane.getWaitingTime(lane) for lane in lanes
                ]
                total_wait_time = sum(lane_wait_times)
                print(total_wait_time)

                traci.simulationStep()  # Advance the simulation by one step
                time.sleep(0.25)
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