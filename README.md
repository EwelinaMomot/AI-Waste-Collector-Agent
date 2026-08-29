*Read this in other languages: [Polish](README.pl.md)*

---

# 🚛♻️ Smart Garbage Truck

## About the Project

**Smart Garbage Truck** is a simulation of an autonomous agent operating in an urban environment. The agent independently analyzes its situation, plans its route, manages fuel, makes logistical decisions, and verifies the correctness of waste segregation using artificial intelligence.

The project combines classical artificial intelligence algorithms, machine learning, and computer vision in a single, cohesive simulation.

---

## Project Goals

✅ Route optimization
✅ Smart resource management
✅ Dynamic environment simulation
✅ Utilization of a custom ID3 decision tree implementation
✅ Utilization of a genetic algorithm for waste collection schedule optimization
✅ Utilization of a custom A* algorithm implementation
✅ Integration of a CNN neural network for waste classification
✅ Demonstration of multiple AI techniques cooperating within a single system

---

# Artificial Intelligence Architecture

## Decision Module - ID3

The agent makes decisions based on:

* ⛽ fuel level,
* ⚖️ current payload,
* 🌦️ weather conditions,
* 🍃 season,
* 🗓️ day of the week,
* 📍 distance to the destination,
* 💸 estimated travel costs.

### Possible Decisions

| Decision | Description |
| ------- | ---------------------- |
| HOUSE   | Waste collection       |
| STATION | Refueling              |
| DUMP    | Emptying the garbage truck |

---

## Route Optimization Module - Genetic Algorithm

Instead of shortsightedly choosing the nearest destination, the agent uses a genetic algorithm to plan a global, optimal visiting route for a given day (Traveling Salesperson Problem - TSP).

* **Selection:** Roulette wheel rule favoring the best (shortest) routes.

* **Reproduction:** Crossover and mutation operations ensuring genetic diversity in subsequent generations.

* **Evolution:** Generational loop finding the most optimal path to minimize fuel consumption.

---

## Pathfinding Module - A*

After selecting a destination, the agent runs the **A*** algorithm and finds the optimal path considering:

* terrain cost,
* turning cost,
* fuel consumption,
* current weather,
* weight of the transported waste.

> The genetic algorithm determines the global order of visiting houses, and then the A* algorithm is used to determine the exact path between the specific, selected points.

---

## Computer Vision Module - CNN

Before collecting waste, the agent performs an automatic inspection of the bin's contents.

The neural network classifies images into one of the following categories:

* 📰 Paper
* 🍼 Plastic and metal
* 🥂 Glass
* 🍎 Bio
* 🗑️ Mixed waste

> The model was trained using a dataset downloaded from the [Kaggle](https://www.kaggle.com/) platform. The full dataset is located in the `dataset_images/` directory.

If the actual contents of the bin do not match the resident's declaration, the collection is rejected.

---

# Dynamic Environment

## Weather

Available weather conditions:

* ☀️ Sunny
* 🌧️ Rainy
* ❄️ Snowy

The weather directly affects:

* movement costs,
* fuel consumption,
* the agent's efficiency.

---

## Seasons

The simulation includes all seasons:

* Spring
* Summer
* Autumn
* Winter

Each season generates different types and quantities of waste.

---

## Collection Schedule

Each day of the week has its own collection schedule for specific waste fractions.

---

# Resource Management

The agent constantly monitors:

* fuel level,
* current capacity of the garbage truck,
* weight of the transported waste,
* position on the map,
* current environmental conditions.

This allows it to predict action costs and make safe decisions.

---

# Project Structure

```text
📦 inteligentna-smieciarka
┣ 📂 agent/            # autonomous agent logic
┣ 📂 environment/      # simulation environment
┣ 📂 genetic/          # genetic algorithm and operators implementation
┣ 📂 search/           # navigation algorithms (A*, BFS)
┣ 📂 ml/               # artificial intelligence modules
┣ 📂 dataset_images/   # dataset for CNN
┣ 📂 assets/           # graphics and visual assets
┣ 📂 output/           # generated decision trees
┗ 📜 main.py           # simulation startup
```

---

# Technologies Used

| Area                 | Technology  |
| -------------------- | ----------- |
| Programming Language | Python      |
| Simulation           | Pygame      |
| Machine Learning     | PyTorch     |
| Data Analysis        | Pandas      |
| Computer Vision      | Torchvision |
| Image Processing     | Pillow      |

---
<video src="assets\demo_videos\videodemo.mp4" width="100%" controls></video>

# Running the Project

> Python **3.9+** is required for the proper functioning of the project and the PyTorch library.

## 1️⃣ Installing Dependencies

```bash
pip install -r requirements.txt
pip install torch torchvision
```

## 2️⃣ Running the Simulation

```bash
python main.py
```

---

# Controls

| Key     | Function                            |
| ------- | ----------------------------------- |
| `SPACE` | Execute the next agent decision     |
| `N`     | Move to the next day                |
| `G`     | Run the genetic algorithm           |

---

# Team and Responsibilities

## Rafał Kotarski

**Responsibility:** search algorithms, system integration, and visual layer.

* Project initialization and repository configuration
* Implementation of the main program loop
* Implementation of BFS and A* algorithms
* Integration of AI models with the agent and user interface
* Exporting the decision tree to `.txt` and `.dot` formats
* Training and integration of the decision tree
* Visualization of waste classification results
* Development of the project's visual layer
* Integration of the genetic algorithm with the application's operation
* Integration of all system modules

---

## Martyna Grochocińska

**Responsibility:** simulation environment, planning logic, and AI integration.

* Design and implementation of the Grid environment
* Generation of the map and environment objects
* Implementation of search logic
* Navigation expansion and transition from BFS to A*
* Development of tile costs and weights
* Integration of ID3 predictions with the agent
* Travel cost estimation mechanism
* Integration of CNN with the agent
* Implementation of the start_pos parameter for the genetic algorithm and logging system improvement

---

## Ewelina Momot

**Responsibility:** agent architecture and deep learning.

* Implementation of the agent architecture
* Movement and knowledge representation mechanisms
* Fuel, capacity, and waste mass management
* Modeling the impact of weight on fuel consumption
* Partial waste collection functionality
* Preparation of the dataset for machine learning
* Automatic gameplay functionality for data generation
* Design, implementation, and training of the neural network
* Training process optimization
* Implementation of crossover, mutation operations, and the evolve function in the genetic algorithm

---

## Maja Radowska

**Responsibility:** decision system, dynamic environment, and user interface.

* Implementation of the ID3 algorithm
* Construction of the time, weather, and season system
* Waste collection schedule
* Environment models (house, gas station, dump)
* Weather effects and visualizations
* A* operation heatmap
* Integration of graphic assets
* Preparation of image datasets
* Implementation of the genetic algorithm engine and selection mechanism (roulette wheel)
* Project documentation

---

## Additional Information

The project was developed as part of the course: **Artificial Intelligence**