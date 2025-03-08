# TrafficLightRL: University of Toronto

---

As University students, we were curious how this project might be able to improve our own daily lives. Thus we trained and tested an RL agent on the University Ave and Union St intersection at Queen's University, and the results are as follows. In each of the graphs we evaluated the RL agent on varying traffic densities, with each point representing the average of 100 episodes to ensure statistical reliability and smooth distributions.

---

## 🎥 Demo Video (Green = Traditional System, Blue = RL Agent)
![Demo Video Placeholder]()

---

## 🖼️ Simulation vs. Reality
Our network was generated from OpenStreetMap data. While pedestrian crosswalks and streetcars were omitted due to export limitations, this does not impact the core RL functionality.
![Map View Placeholder](./documentation/Queens.png)

---

## 🚦 Results

📉 Wait Time Reduction:
- Low Traffic: 15% decrease
- Medium Traffic: 27% decrease
- High Traffic: 34% decrease

![Wait Times Graph Placeholder](./documentation/mean_wait_time_plot_final2.png)

🌱 Emissions Reduction:
- Low Traffic: 33% decrease
- Medium Traffic: 35% decrease
- High Traffic: 40% decrease

![Emissions Graph Placeholder](./documentation/mean_emissions_plot_final2.png)

---

## 🚀 Future Enhancements

- Implement TTC Priority Signals: The model will detect approaching streetcars and buses to adjust signal timing dynamically, minimizing delays for public transit users.
- Pedestrian Consideration: Improve network accuracy by integrating pedestrian crossings.
- Expand the RL model to multiple intersections in downtown Toronto, integrating it with the city's smart traffic management system.

Our results demonstrate RL’s potential to revolutionize traffic management—making within communities across the GTA. Implementation of this project would make roads safer, more efficient, and environmentally friendly for Students at the University of Toronto, and members of the community.
