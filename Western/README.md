# TrafficLightRL: Western University

---

## 🚦 Brief Description
TrafficLightRL is a project dedicated to optimizing traffic light control systems using reinforcement learning (RL). The Western University branch of the project focuses on the intersection of Sarnia Rd & Philip Aziz Ave, near Western University in London, ON. By integrating advanced machine learning techniques with real-world urban infrastructure data, the project aims to enhance traffic flow and reduce congestion.

The evaluation process involves testing the RL agent across various traffic densities. Each data point in the presented graphs represents the average performance over 100 episodes, ensuring statistical reliability and smooth distributions.

---

## 🎥 Demo Video (Green = Traditional System, Blue = RL Agent)
![Demo Video Placeholder](./documentation/demo_video_western.mp4)

---

## 🖼️ Simulation vs. Reality
The network for this geographical location was generated using OpenStreetMap data and exported to a SUMO network via the OSM Web Wizard. Although pedestrian crosswalks were omitted due to export limitations, this omission does not affect the core functionality of the RL system.
![Map View Placeholder](./documentation/western_map_image.png)

---

## 🚦 Results

📉 Wait Time Reduction:
- Low Traffic: 13% decrease
- Medium Traffic: 24% decrease
- High Traffic: 19% decrease

![Wait Times Graph Placeholder](./documentation/mean_wait_time_plot_final2.png)

🌱 Emissions Reduction:
- Low Traffic: 10% decrease
- Medium Traffic: 23% decrease
- High Traffic: 29% decrease

![Emissions Graph Placeholder](./documentation/mean_emissions_plot_final2.png)

---

🚀 Future Enhancements

- Pedestrian Consideration and Bus Stops: Improve network accuracy by integrating pedestrian crossings and existing bus stops.
- Expanded Deployment: Apply the model to additional real-world locations.

The results demonstrate the potential of RL to revolutionize traffic management within the Western community. Implementing this project would create safer, more efficient, and environmentally friendly roads for students, faculty, and community members.
