import numpy as np
import random
import gymnasium
import sumolib
import time
import traci
import os


class SumoEnv(gymnasium.Env):
  def __init__(self, use_gui=True, use_random=False, use_actions=True):
    super().__init__() # Initializes the parent class

    # Check if TraCI is already loaded; if so, close it
    if traci.isLoaded():
      traci.close()

    # Define the Discrete action space with gymnasium.spaces.Discrete(n)
    # choices are up & down = green, or l & r = green
    self.action_space = gymnasium.spaces.Discrete(4)

    # Define the Box observation space with gymnasium.spaces.Box()
    # Note the structure of the Box parameters requires NumPy arrays!
    self.lanes = {
      # Edge 1 (East incoming)
      "466414380#0_0": {"type": [0, 1, 1], "phases": [0]},  # Right-turn/straight lane
      "466414380#0_1": {"type": [0, 1, 0], "phases": [0]},  # Straight lane
      "466414380#0_2": {"type": [0, 1, 0], "phases": [2]},  # Left-turn/U-turn lane

      # Edge 2 (West incoming)
      "466414379#0_0": {"type": [0, 1, 1], "phases": [0]},  # Right-turn/straight lane
      "466414379#0_1": {"type": [0, 1, 0], "phases": [0]},  # Straight lane
      "466414379#0_2": {"type": [1, 0, 0], "phases": [2]},  # Left-turn/U-turn lane

      # Edge 3 (South incoming)
      "25634438#0_2": {"type": [1, 0, 0], "phases": [6]},  # Left-turn/U-turn lane
      "25634438#0_1": {"type": [0, 1, 0], "phases": [4]},  # Straight lane
      "25634438#0_0": {"type": [0, 1, 1], "phases": [4]},  # Right-turn/Straight lane

      # Edge 4 (North incoming)
      "466414089#1_2": {"type": [1, 0, 0], "phases": [6]},  # Left-turn/U-turn lane
      "466414089#1_1": {"type": [0, 1, 0], "phases": [4]},  # Straight lane
      "466414089#1_0": {"type": [0, 1, 1], "phases": [4]}  # Right-turn/Straight lane
    }

    self.last_phase_change_time = {
      0: 0,
      2: 0, 
      4: 0,
      6: 0
    }
    
    max_cars = 30 # CHANGE FOR ACTUAL MAX. NUMBER OF CARS
    self.max_cars = max_cars
    
    self.car_spawn_rate = 0.3 # cars spawn at 30% chance

    # np array structure: [traffic_light_phase][positions][speeds], dtype=np.float32
    self.observation_space = gymnasium.spaces.Box(
      low=np.array([0] + [-np.inf] * (2 * max_cars) + [0] * max_cars),
      high=np.array([8] + [np.inf] * (2 * max_cars) + [np.inf] * max_cars),
      dtype=np.float32
    )
    
    # Upon each render of the SumoEnv Class, we should start the simulation
    # Implement the sumo_binary, sumo_config, and traci.start from test_demo.py
    self.use_gui = use_gui
    if use_gui:
      sumo_binary = sumolib.checkBinary('sumo-gui')
    else:
      sumo_binary = sumolib.checkBinary('sumo')

    # use the proper .sumocfg file depending on if want predefined or random cars
    self.use_random = use_random
    if use_random:
      sumo_config = "./Network/waterloo.sumocfg"
    else:
      sumo_config = "./Network/waterloo.sumocfg"

    # used to track number of deployed cars
    if self.use_random:
      self.deployed_counter = 0
    else:
      self.deployed_counter = 1

    # store these variables for use later
    self.sumo_binary = sumo_binary
    self.sumo_config = sumo_config

    # Start the simulation
    self.started = False

    # Track cumulative metrics
    self.vehicle_wait_log = {}
    self.total_congestion_log = []
    self.total_speed_log = []

    # use actions argument: False = use the timer based system instead (for comparing between agent and real-life)
    self.use_actions = use_actions

    # Define consistent pause time for sumo-gui visualization
    self.pause_time = 0.25

  def step(self, action):
    # On first step, start the traci sim
    if not self.started:
      traci.start([self.sumo_binary, "--start", "-c", self.sumo_config], port=8813)
      self.started = True
      traffic_light_id = traci.trafficlight.getIDList()[0] # MAKE SURE TO MODIFY IF YOUR INTERSECTION CONTAINS >1 TRAFFIC LIGHT
      traci.trafficlight.setPhase(traffic_light_id, 0)
          # Ensure light phases are all manually controlled

      if self.use_actions:
        traci.trafficlight.setPhaseDuration(traffic_light_id, 99999)  # Hold this phase indefinitely
    
    # Perform the action
    if self.use_actions:
      self.perform_action(action)
    
    # Spawn in a car if suits the spawn rate on step
    if self.use_random:
      if (random.random() < self.car_spawn_rate) and (self.deployed_counter < self.max_cars):
        self.spawn_random_car(self.deployed_counter)
        self.deployed_counter += 1
  

    # Advance the simulation by one step
    traci.simulationStep()
    if self.use_gui: # pause in between steps to slow down if in 'simulation mode'
      time.sleep(self.pause_time) 
    #print("Step: " + str(traci.simulation.getTime()))
    # Get the new state
    observation = self.get_state()

    # Calculate the reward
    reward = self.calculate_reward()

    # Determine if simulation is done
    done = self.is_done()

    # Set placeholder for info -> returns the tracked cumulative metrics IF done
    info = {
      "vehicle_wait_log": self.vehicle_wait_log if done else None,
      "total_congestion_avg": (sum(self.total_congestion_log) / len(self.total_congestion_log)) if done and self.total_congestion_log else None,
      "total_speed_avg": (sum(self.total_speed_log) / len(self.total_speed_log)) if done and self.total_speed_log else None
    }

    # Set placeholder for truncated
    truncated = False

    # set 'observation' to a numpy array
    observation = np.array(observation, dtype=np.float32)

    # Return step information (MUST follow this order of variables!!!)
    return observation, reward, done, truncated, info

  def render(self):
    # render needs to exist in the Gymnasium env, as it is an essential aspect
    # however we might not need to put anything inside it, hence 'pass'
    # this depends on if the command -> traci.simulationStep() exists somewhere else in the Class
    pass

  def reset(self, seed=None, options=None):

    # resets the gymnasium.Env parent class
    super().reset(seed=seed)

    # close the simulation (reset)
    if not self.use_gui: # traci.load() doesn't work for sumo-gui - i.e. can only run once
      traci.load(["-c", self.sumo_config])

    # reset counter variables
    if self.use_random:
      self.deployed_counter = 0
    else:
      self.deployed_counter = 1

    # convert 'observation' to a NumPy array
    observation = np.array(self.get_state(), dtype=np.float32)

    # return 'observation' and 'info' --> MUST be in this form
    return observation, {}

  def get_state(self):
    # Define a speed threshold for "stopped" vehicles
    speed_threshold = 0.1  # Vehicles with speed < 0.1 m/s are considered stopped

    state = []

    # 1. Traffic light phase (normalized to [0, 1])
    traffic_light_phase = traci.trafficlight.getPhase(traci.trafficlight.getIDList()[0])
    state.append(traffic_light_phase / 9.0)  # Normalize phase to [0, 1]
    for phase_change_time in self.last_phase_change_time:
      if phase_change_time == traffic_light_phase:
        self.last_phase_change_time[phase_change_time] = 0
      else:
        self.last_phase_change_time[phase_change_time] += 1

    # 2. Time since last phase change (normalized to [0, 1])
    current_time = traci.simulation.getTime()
    time_since_last_change = current_time - min(self.last_phase_change_time.values())
    state.append(time_since_last_change / self.max_wait_time)  # Normalize using max_wait_time

    # 3. Per-lane metrics (only for lanes directly connected to the intersection)
    for lane_id, lane_info in self.lanes.items():
        vehicle_ids = traci.lane.getLastStepVehicleIDs(lane_id)

        # Number of vehicles (normalized to [0, 1])
        num_vehicles = len(vehicle_ids)
        state.append(num_vehicles / self.max_cars)

        # Queue length (number of vehicles with speed < threshold, normalized to [0, 1])
        queue_length = sum(1 for v_id in vehicle_ids if traci.vehicle.getSpeed(v_id) < speed_threshold)
        state.append(queue_length / self.max_cars)

        # Total wait time (normalized to [0, 1])
        total_wait_time = sum(traci.vehicle.getWaitingTime(v_id) for v_id in vehicle_ids)
        state.append(total_wait_time / self.max_wait_time)  # Normalize using max_wait_time

        # Average speed (normalized to [0, 1])
        avg_speed = np.mean([traci.vehicle.getSpeed(v_id) for v_id in vehicle_ids]) if vehicle_ids else 0
        state.append(avg_speed / traci.lane.getMaxSpeed(lane_id))  # Normalize to [0, 1]

        # Time since last visited  
        minn = float("inf")
        for phase in lane_info["phases"]:
          if self.last_phase_change_time[phase] < minn:
            minn = self.last_phase_change_time[phase]
        state.append(minn / float(max(self.last_phase_change_time.values())))

        # Lane type (one-hot encoded)
        lane_type = lane_info["type"]
        state.extend(lane_type)

    return np.array(state, dtype=np.float32)

  def perform_action(self, action):

    light_id = traci.trafficlight.getIDList()[2]
    current_phase = traci.trafficlight.getPhase(light_id)
   
    """
    Phases: 
      (0) E & W = green, N & S = red
      (1) E & W = yellow, N & S = red
      (2) E & W left turn/U-turn = green, N & S = red
      (3) E & W left turn/U-turn = yellow, N & S = red
      (4) E & W = red, N & S = green
      (5) E & W = red, N & S = yellow
      (6) E & W = red, N & S left turn/U-turn = green 
      (7) E & W = red, N & S left turn/U-turn = yellow 

      Define action 0 as switching green to E & W; thus turning N & S red
      Define action 1 as switching green to E & W left turn/U-turn; thus turning all straight and right turns red
      Define action 2 as switching green to N & S; thus turning E & W red
      Define action 3 as switching green to N & S left turn/U-turn; thus turning all straight and right turns red

      Also, no actions can be performed during yellow light!
    """
    if action == 0 and current_phase != 0:
      traci.trafficlight.setPhase(light_id, 1)  # transition to yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)  # set yellow duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 0)  # set E-W green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
      self.skip_steps(5) # ensure light is green for at least 3 seconds

    elif action == 1 and current_phase != 2:
      traci.trafficlight.setPhase(light_id, 1)  # E-W yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 2)  # set E-W left turn/U-turn green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
      self.skip_steps(5)

    elif action == 2 and current_phase != 4:
      traci.trafficlight.setPhase(light_id, 4)  # Set N-S green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold green indefinitely
      self.skip_steps(5)  # Ensure light stays green for at least 3 seconds
      
      traci.trafficlight.setPhase(light_id, 5)  # Transition to N-S yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)
      self.skip_steps(3)

    elif action == 3 and current_phase != 6:
      traci.trafficlight.setPhase(light_id, 6)  # Set N-S left turn/U-turn green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold green indefinitely
      self.skip_steps(5)  # Ensure light stays green for at least 3 seconds
      
      traci.trafficlight.setPhase(light_id, 7)  # Transition to N-S left turn yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)
      self.skip_steps(3)


  def calculate_reward(self):
    # REWARD FUNCTION: Calculate the reward (should be negative if in a poor state i.e. high congestion)
    lane_ids = self.lanes.keys()
    vehicle_ids = traci.vehicle.getIDList()
    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)
    reward = 0
    try:

      for lane in self.lanes.keys():
        if current_phase in self.lanes[lane]["phases"]:
          reward += len(traci.lane.getLastStepVehicleIDs(lane))

        else:
          cur_wait_time = traci.lane.getWaitingTime(lane)
          cur_phases = self.lanes[lane]["phases"]
          min_phase = cur_phases[0]
          for j in range(1, len(cur_phases)):
            if self.last_phase_change_time[cur_phases[j]] < self.last_phase_change_time[min_phase]:
              min_phase = cur_phases[j]
          reward -= cur_wait_time * (self.last_phase_change_time[min_phase] / max(self.last_phase_change_time.values()))

      congestion = self.calculate_congestion(vehicle_ids)
      wait_time = self.calculate_avg_wait_time(lane_ids)
      stops = self.calculate_total_stops(lane_ids)
      avg_speed = self.calculate_avg_speed(vehicle_ids)# -> would be maximize so don't multiply by -1
      #reward = -1*(0.5*congestion + 0.8*wait_time + stops) + 0.75*avg_speed # minimize all terms

    except:

      print("BIG NONO")
      reward = 0

    return reward

  def skip_steps(self, x):
    for _ in range(x): 
      if self.use_random:
        if (random.random() < self.car_spawn_rate) and (self.deployed_counter < self.max_cars):
          self.spawn_random_car(self.deployed_counter)
          self.deployed_counter += 1
    

      # Advance the simulation by one step
      traci.simulationStep()
      if self.use_gui: # pause in between steps to slow down if in 'simulation mode'
        time.sleep(self.pause_time)

  def is_done(self):
    max_time = self.max_wait_time  # Example maximum simulation time
    return (traci.simulation.getTime() >= max_time or len(traci.vehicle.getIDList()) == 0) and self.deployed_counter >= self.max_cars -1


  # METRICS:
  def calculate_congestion(self, vehicle_ids):
    congestion = 0
    current_time = traci.simulation.getTime()  # Get the current simulation time
    
    for vehicle_id in vehicle_ids:
      departure_time = traci.vehicle.getDeparture(vehicle_id)  # Get each vehicle's departure time
      speed = traci.vehicle.getSpeed(vehicle_id)  # Get the vehicle's current speed
      
      # Check if the vehicle is stopped and not just starting/departing
      if speed == 0 and current_time not in range(int(departure_time) - 1, int(departure_time) + 2):
          congestion += 1  # Increment congestion counter for stopped vehicles
  
    # update congestion log
    self.total_congestion_log.append(congestion)

    return congestion

  def calculate_avg_wait_time(self, lane_ids):
    wait_times = []
    
    # total wait time of cars in all lanes
    for lane_id in lane_ids:
      # total wait time of all cars in one lane
      for vehicle_id in traci.lane.getLastStepVehicleIDs(lane_id):
          wait_time = traci.vehicle.getWaitingTime(vehicle_id)

          # update the wait log
          if vehicle_id in self.vehicle_wait_log:
            self.vehicle_wait_log[vehicle_id] = max(self.vehicle_wait_log[vehicle_id], wait_time) # only want the greatest average wait time for each vehicle
          else:
            self.vehicle_wait_log[vehicle_id] = wait_time

          wait_times.append(wait_time)
  
    avg_wait_time = sum(wait_times)/len(wait_times) if wait_times else 0
    
    return avg_wait_time

  def calculate_total_stops(self, lane_ids):
    total_stops = 0
    for lane_id in lane_ids:
      stops_in_lane = traci.lane.getLastStepHaltingNumber(lane_id)
      total_stops += stops_in_lane

    return total_stops
    
  def calculate_avg_speed(self, vehicle_ids):
    total_speed = sum(traci.vehicle.getSpeed(v_id) for v_id in vehicle_ids)
    avg_speed = total_speed / len(vehicle_ids) if vehicle_ids else 0

    # update total speed log
    self.total_speed_log.append(avg_speed)

    return avg_speed

  def spawn_random_car(self, step_counter):
    """
    Spawns a random car with a unique ID and assigns it a random route.
    edge_mapping represents the available routes that any car can take; start_edge:end_edge
    """
    edge_mapping = {
        "183330267": ["401622262", "156268074", "-864501901#0"], # East starting -> [right, stright, left]
        "150872238#0": ["-864501901#0", "262794389#4", "401622262"], # West starting -> [right, straight, left]
        "864501901#0": ["262794389#4", "401622262", "156268074"], # South starting -> [right, straight, left]
        "401622246#0": ["156268074", "-864501901#0", "262794389#4"] # North starting -> [left, straight, right]
    }
    vehicle_id = f"rand_car_{step_counter}"

    start_edge = random.choice(list(edge_mapping.keys()))
    end_edge = random.choice(edge_mapping[start_edge])

    route_id = f"route_{vehicle_id}"

    try:
        traci.route.add(routeID=route_id, edges=[start_edge, end_edge])

        # Add the vehicle to the simulation
        traci.vehicle.add(vehID=vehicle_id, routeID=route_id)

        #print(f"Deployed random vehicle {vehicle_id} from {start_edge} to {end_edge}")

        # Set a random speed for the vehicle
        traci.vehicle.setSpeed(vehicle_id, random.uniform(5, 15))

    except traci.TraCIException as e:
        pass
        #print(f"Failed to add vehicle {vehicle_id} on route from {start_edge} to {end_edge}: {e}")



env = SumoEnv(use_gui=True, use_random=True, use_actions=False) # use_gui=False sets sumo_binary to 'sumo' instead of 'sumo-gui'

episodes = 1 # note can only be run ONCE with sumo-gui!
score_log = []
wait_log = []

congestion_log = []
speed_log = []
emissions_log = []

for episode in range(1, episodes + 1):
    done = False
    truncated = False
    score = 0
    info = {}

    while not done:
        env.render()
        action = env.action_space.sample()
        state, reward, done, truncated, info = env.step(action)
        score += reward

    state, info = env.reset()
    score_log.append(score)

    # Extract wait time metrics
    wait_times = info.get("vehicle_wait_log", {}).values()
    total_wait_time = sum(wait_times)
    num_cars = len(wait_times)
    episode_mean_wait = total_wait_time / num_cars if num_cars > 0 else 0
    wait_log.append(episode_mean_wait)

    # Extract congestion and speed metrics
    if info.get("total_congestion_avg") is not None:
        congestion_log.append(info["total_congestion_avg"])
    if info.get("total_speed_avg") is not None:
        speed_log.append(info["total_speed_avg"])

traci.close()

# Compute and print final metrics
mean_sample_score = np.mean(score_log)
mean_wait_time = np.mean(wait_log)
mean_congestion = np.mean(congestion_log) if congestion_log else None
mean_speed = np.mean(speed_log) if speed_log else None


print(f"Mean Score over {episodes} episodes: {mean_sample_score}")
print(f"Mean wait time over {episodes} episodes: {mean_wait_time}")
print(f"Mean congestion over {episodes} episodes: {mean_congestion}")
print(f"Mean speed over {episodes} episodes: {mean_speed}")
