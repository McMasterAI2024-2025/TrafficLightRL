# TrafficLightRL: McMaster University

---

## 🚦 Brief Description
TrafficLightRL is a project focused on using reinforcement learning to optimize traffic light control systems at [University Name]. This project integrates advanced machine learning techniques with real-world urban infrastructure data to improve traffic flow and reduce congestion.

**^^ will update the above text later on! it'll be good to include a bunch of metrics somewhere in this file as well. The purpose of this is to help you for example if you were in a job interview and you wanted to explain your contributions to the project this can help you explain to the recruiter your work so definitely put some thought into this**

---

## 🖼️ Google Maps View
![Map View Placeholder](./documentation/mcmaster_map_image.png)

---

## 🎥 Demo Video (Green = Traditional System, Blue = RL Agent)
![Demo Video Placeholder](./documentation/demo_vid.gif)

---

## 📄 Challenges and Future Considerations
If you take a look at the SUMO network you will notice that there are no pedestrian crosswalks. Unfortunately OSM Web Wizard is not quite perfect, and was unable to export a network that accurately reflected the actual map while including pedestrian crosswalks. While I acknowledge this as a current flaw in the agent's ability to "simulate reality", I believe that the strong metrics outlined earlier emphasize the applicability of RL in this context. 

As seen in the top right of the map view, this intersection is directly connected to the McMaster Children's Hospital. In the future I would like to implement additional functionality of our agent to be able to prioritize emergency vehicles both leaving and going to the hospital, to ensure our solution puts the health needs of the community first. 
