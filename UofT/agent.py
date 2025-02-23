
import numpy as np
import random
import gymnasium
import traci
import sumolib
import time
import os

class SumoEnv(gymnasium.Env):
  def __init__(self, use_gui=False, use_random=False, use_actions=True):
    super().__init__() # Initializes the parent class

    # Check if TraCI is already loaded; if so, close it
    if traci.isLoaded():
      traci.close()

    # Define the Discrete action space with gymnasium.spaces.Discrete(n)
    # choices are up & down = green, or l & r = green
    self.action_space = gymnasium.spaces.Discrete(4)

    # Define the Box observation space with gymnasium.spaces.Box()
    # Note the structure of the Box parameters requires NumPy arrays!
    
    max_cars = 20 # CHANGE FOR ACTUAL MAX. NUMBER OF CARS
    self.max_cars = max_cars
    
    self.car_spawn_rate = 0.3 # cars spawn at 30% chance

    # np array structure: [traffic_light_phase][positions][speeds], dtype=np.float32
    self.observation_space = gymnasium.spaces.Box(
      low=np.array([0] + [-np.inf] * (2 * max_cars) + [0] * max_cars),
      high=np.array([3] + [np.inf] * (2 * max_cars) + [np.inf] * max_cars),
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
      sumo_config = os.path.join(os.path.dirname(__file__), 'network/uoft.sumocfg')

    else:
      sumo_config = os.path.join(os.path.dirname(__file__), 'network/uoft.sumocfg')


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
    self.pause_time = 0.1

  def step(self, action):
    # On first step, start the traci sim
    if not self.started:
      traci.start([self.sumo_binary, "--start", "-c", self.sumo_config])
      self.started = True
      traffic_light_id = traci.trafficlight.getIDList()[0]
      traci.trafficlight.setPhase(traffic_light_id, 0)
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
    print("Step: " + str(traci.simulation.getTime()))
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
    # Get the traffic light phase
    traffic_light_ids = traci.trafficlight.getIDList()
    traffic_light_phase = traci.trafficlight.getPhase(traffic_light_ids[0]) # only 1 in this network

    # Get vehicle IDs and limit to max_cars
    vehicle_ids = traci.vehicle.getIDList()

    # Collect positions and speeds, padding if fewer than max_cars
    positions = []
    speeds = []
    for v_id in vehicle_ids:
      position = traci.vehicle.getPosition(v_id)  # Returns (x, y) tuple
      speed = traci.vehicle.getSpeed(v_id)
      positions.extend(position)  # Add x, y to positions list
      speeds.append(speed)

    # Pad positions and speeds if there are fewer than max_cars vehicles
    if len(vehicle_ids) < self.max_cars:
      missing_cars = self.max_cars - len(vehicle_ids)
      positions.extend([0.0, 0.0] * missing_cars)
      speeds.extend([0.0] * missing_cars)

    # Create the state as a numpy array
    obs = np.array([traffic_light_phase] + positions + speeds, dtype=np.float32)
    return obs

  def perform_action(self, action):

    light_id = traci.trafficlight.getIDList()[0]
    current_phase = traci.trafficlight.getPhase(light_id)

    """
    Phases: 
      (0) E & W = green, N & S = red
      (1) E & W = yellow, N & S = red
      (2) all red
      (3) E & W = red, N & S turn/U-turn, green
      (4) E & W = red, N & S turn/U-turn, yellow
      (5) all red
      (6) E & W = red, N & S = green 
      (7) E & W = red, N & S left turn/U-turn = green, straight = yellow 
      (8) E & W = red, N & S left turn/U-turn = green (only good one)
      (9) E & W = red, N & S left turn/U-turn = yellow
      (10) all red 
      (11) - (13) duplicates -> note to self, lines going E&W are for the streetcart, so not bugged!
      
      Define action 0 as switching green to E & W; thus turning N & S left turns yellow (9), then red (10), then E&W green (0)
      Define action 1 as switching green to N left turn/U-turn for streetcars; thus make E&W yellow (1) then red (2) then make N left turns green (3)
      Define action 2 as switching green to N&S both; thus make turn yellow (4) then red (5) then make N&S green (6)
      Define action 3 as switching green to S left turn; thus make straights yellow (7), then make straights red (8)
    """

    if action == 0 and current_phase != 0:
      traci.trafficlight.setPhase(light_id, 9)  # transition to yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)  # set yellow duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 10)  # all red
      traci.trafficlight.setPhaseDuration(light_id, 1)  # set red duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 0)  # set E-W green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
      self.skip_steps(5) # ensure light is green for at least 3 seconds

    elif action == 1 and current_phase != 3:
      traci.trafficlight.setPhase(light_id, 1)  # transition to yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)  # set yellow duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 2)  # all red
      traci.trafficlight.setPhaseDuration(light_id, 1)  # set red duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 3)  # let streetcars pass
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
      self.skip_steps(5) # ensure light is green for at least 3 seconds

    elif action == 2 and current_phase != 6:
      traci.trafficlight.setPhase(light_id, 4)  # transition to yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)  # set yellow duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 5)  # all red
      traci.trafficlight.setPhaseDuration(light_id, 1)  # set red duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 6)  # set N-S green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # Hold this phase indefinitely
      self.skip_steps(5) # ensure light is green for at least 3 seconds

    elif action == 3 and current_phase != 8:
      traci.trafficlight.setPhase(light_id, 7)  # transition to yellow
      traci.trafficlight.setPhaseDuration(light_id, 4)  # set yellow duration
      self.skip_steps(3)
      traci.trafficlight.setPhase(light_id, 8)  # straights red, left turns green
      traci.trafficlight.setPhaseDuration(light_id, 99999)  # set red duration
      self.skip_steps(5)

  def calculate_reward(self):
    # REWARD FUNCTION: Calculate the reward (should be negative if in a poor state i.e. high congestion)
    lane_ids = traci.lane.getIDList()
    vehicle_ids = traci.vehicle.getIDList()
    try:
      congestion = self.calculate_congestion(vehicle_ids)
      wait_time = self.calculate_avg_wait_time(lane_ids)
      stops = self.calculate_total_stops(lane_ids)
      avg_speed = self.calculate_avg_speed(vehicle_ids)# -> would be maximize so don't multiply by -1
      reward = -1*(1.5*congestion + 1.5*wait_time + stops) + 0.75*avg_speed # minimize all terms
    except:
      reward = 0

    return reward

  def skip_steps(self, x):
    for _ in range(x): 
      traci.simulationStep()
      if self.use_gui:
        time.sleep(self.pause_time)

  def is_done(self):
    max_time = 1000  # Example maximum simulation time
    return (traci.simulation.getTime() >= max_time or len(traci.vehicle.getIDList()) == 0) and self.deployed_counter != 0


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
    #north traffic light
    #'466414089#0':'466414089#1', 
    '466414089#1':'35519718#1',
    '466414089#1':'182704478#1',
    '466414089#1':'184789522#1',
    
    #west traffic light
    #'42684286':'466414379#0', 
    '466414379#0':'35519718#1',
    '466414379#0':'182704478#1',
    '466414379#0':'184789522#1',
    '466414379#0':'50876968#1',
    
    #south traffic light
    '25634438#0':'35519718#1',
    '25634438#0':'50876968#1',
    '25634438#0':'184789522#1',

    #east traffic light
    '466414380#0':'50876968#1',
    '466414380#0':'35519718#1',
    '466414380#0':'182704478#1'
    }
    
    vehicle_id = f"rand_car_{step_counter}"

    edges = traci.edge.getIDList()
    start_edges = []
    for edge in edges:
        if not edge.startswith('-') and not edge.startswith(':') and edge in edge_mapping:
            start_edges.append(edge)
    
    start_edge = random.choice(start_edges)
    end_edge = edge_mapping[start_edge]

    route_id = f"route_{vehicle_id}"

    try:
        traci.route.add(routeID=route_id, edges=[start_edge, end_edge])

        # Add the vehicle to the simulation
        traci.vehicle.add(vehID=vehicle_id, routeID=route_id)

        print(f"Deployed random vehicle {vehicle_id} from {start_edge} to {end_edge}")

        # Set a random speed for the vehicle
        traci.vehicle.setSpeed(vehicle_id, random.uniform(5, 15))

    except traci.TraCIException as e:
        print(f"Failed to add vehicle {vehicle_id} on route from {start_edge} to {end_edge}: {e}")
        


if __name__ == "__main__":
  # the purpose of this is just to visualize our results!
  env = SumoEnv(use_gui=True, use_random=True, use_actions=False) # set use_gui arg to True

  episodes = 10 # note can only be run ONCE with sumo-gui!
  score_log = []
  for episode in range(1, episodes+1):
      #state, _ = env.reset()
      done = False
      truncated = False
      score = 0
      while not done:
          env.render()
          action = env.action_space.sample()
          state, reward, done, truncated, info = env.step(action)
          score+=reward

      score_log.append(score)

  traci.close()
  mean_sample_score = np.mean(score_log)*episodes
  print(f"Mean Score over {episodes} episodes: {mean_sample_score}")
