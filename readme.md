
# 🎈 Ballatics – High-Altitude Balloon Trajectory And Jetstream Tracker

**Ballatics** is a real-time web application for visualizing high-altitude balloon trajectories, computing their speed and altitude, and overlaying wind direction vectors from atmospheric data.
###***GO check it out :*** https://ballatics.onrender.com/
(As it is hosted on render visiting it for the first time might take time as the pods get killed for 50s of inacivity)

## 🌍 Features

- Live tracking of 1000 high-altitude balloons across the globe  
- Hourly trajectory data from Windborne Systems  
- Beautiful Leaflet map with dark mode UI  
- Wind direction arrows using Open-Meteo historical wind data  
- Altitude vs Time plots using Chart.js  
- Automatic backfilling of past 24 hours on server restart  
- Hourly cron-based data fetcher with fault tolerance  

## 🚀 Getting Started

### Prerequisites

- Python 3.8+  
- `pip`  
- Internet connection (for external APIs and map tiles)  

### Installation

```bash
git clone https://github.com/your-username/ballatics.git
cd ballatics
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run the App

```bash
python database.py  # starts the Flask app and begins data fetching
```

Visit [http://localhost:5000](http://localhost:5000) to view the interface.

## 📦 Project Structure

```
ballatics/
├── templates/
│   └── index.html        # Main frontend page
├── static/               # Optional: static assets (e.g., icons, CSS)
├── database.py           # Flask server + scheduler + data logic
├── balloons.db           # SQLite database (auto-created)
├── requirements.txt      # Dependencies
└── README.md             # This file
```

## 🧠 Data Sources

- **Windborne Systems**: Hourly balloon trajectory JSON dumps  
- **Open-Meteo Archive API**: Wind direction and speed (10m altitude)  

## 📈 Future Work

- Support for real-time WebSocket updates  
- Per-hour state filter toggles  
- Multi-balloon comparison view  
- Predictive modeling using historical wind patterns  

## 👨‍💻 Author

Developed with ❤️ by Ninad Chaudhari

## 📄 License

MIT License
