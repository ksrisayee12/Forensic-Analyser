import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import threading
import time
from datetime import datetime, timedelta
import requests

# ====== CONFIG: put your OpenWeather API key here ======
OPENWEATHER_API_KEY = "5b227e14106b0f7f85eaff280c37690b"  # get from https://openweathermap.org/api


class IBMAgriculturalAdvisor:
    def __init__(self, root):
        self.root = root
        self.root.title("IBM AI-Powered Agricultural Advisor")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a2540')  # IBM Dark Blue

        # IBM Color Palette
        self.ibm_primary = '#0a2540'
        self.ibm_secondary = '#0066cc'
        self.ibm_success = '#00aa5e'
        self.ibm_warning = '#ff8f00'
        self.ibm_danger = '#d1291f'
        self.ibm_light = '#f4f4f4'

        # ---------- INITIAL DATA ----------
        self.soil_moisture = 65.0
        self.rain_forecast = 10.0
        self.temperature = 28.0
        self.crop_stage = "Vegetative"
        self.soil_type = "Loam"
        self.history = []          # list of dicts for 7‑day performance
        self.water_saved = 0
        self.running = True

        self.sim_thread_started = False

        self.setup_ui()

        # DO NOT auto‑start simulation here; wait for user to click "Start Simulation"
        # self.start_simulation()

        # Clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ===================== UI SETUP =====================

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.ibm_primary, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="IBM AI-Powered Agricultural Advisor",
            font=('Segoe UI', 18, 'bold'),
            bg=self.ibm_primary,
            fg='white'
        )
        title.pack(pady=20)

        subtitle = tk.Label(
            header_frame,
            text="Soil Biosensor Precision Irrigation System",
            font=('Segoe UI', 12),
            bg=self.ibm_primary,
            fg='#b3d9ff'
        )
        subtitle.pack()

        # Main content
        content_frame = tk.Frame(self.root, bg=self.ibm_light)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Left panel - Sensors & Status
        left_frame = tk.Frame(content_frame, bg=self.ibm_light, relief='raised', bd=2, width=350)
        left_frame.pack(side='left', fill='y', padx=(0, 15), pady=10)
        left_frame.pack_propagate(False)

        # Soil Biosensor Panel
        sensor_title = tk.Label(
            left_frame,
            text="🧪 SOIL BIOSENSOR READINGS",
            font=('Segoe UI', 14, 'bold'),
            bg=self.ibm_light,
            fg=self.ibm_primary
        )
        sensor_title.pack(pady=(20, 10))

        # Soil Moisture
        moisture_frame = tk.Frame(left_frame, bg=self.ibm_light)
        moisture_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(
            moisture_frame,
            text="Soil Moisture:",
            font=('Segoe UI', 12, 'bold'),
            bg=self.ibm_light
        ).pack(anchor='w')

        self.moisture_var = tk.StringVar(value="65%")
        moisture_label = tk.Label(
            moisture_frame,
            textvariable=self.moisture_var,
            font=('Segoe UI', 24, 'bold'),
            bg=self.ibm_light,
            fg=self.ibm_secondary
        )
        moisture_label.pack()

        self.moisture_progress = ttk.Progressbar(
            moisture_frame,
            length=300,
            mode='determinate'
        )
        self.moisture_progress.pack(fill='x', pady=(5, 15))

        # Weather Panel
        weather_title = tk.Label(
            left_frame,
            text="🌤️ WEATHER FORECAST",
            font=('Segoe UI', 14, 'bold'),
            bg=self.ibm_light,
            fg=self.ibm_primary
        )
        weather_title.pack(pady=(20, 10))

        weather_frame = tk.Frame(left_frame, bg=self.ibm_light)
        weather_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(
            weather_frame,
            text="Rain Probability (24h):",
            font=('Segoe UI', 12, 'bold'),
            bg=self.ibm_light
        ).pack(anchor='w')

        self.rain_var = tk.StringVar(value="10%")
        rain_label = tk.Label(
            weather_frame,
            textvariable=self.rain_var,
            font=('Segoe UI', 18, 'bold'),
            bg=self.ibm_light,
            fg=self.ibm_warning
        )
        rain_label.pack()

        tk.Label(
            weather_frame,
            text="Temperature:",
            font=('Segoe UI', 12, 'bold'),
            bg=self.ibm_light
        ).pack(anchor='w', pady=(10, 0))

        self.temp_var = tk.StringVar(value="28°C")
        temp_label = tk.Label(
            weather_frame,
            textvariable=self.temp_var,
            font=('Segoe UI', 16),
            bg=self.ibm_light,
            fg=self.ibm_secondary
        )
        temp_label.pack(pady=(0, 15))

        # Center - AI Decision Engine
        decision_frame = tk.Frame(content_frame, bg='#ffffff', relief='raised', bd=3)
        decision_frame.pack(side='left', fill='both', expand=True, padx=(0, 15), pady=10)

        tk.Label(
            decision_frame,
            text="🤖 IBM AI DECISION ENGINE",
            font=('Segoe UI', 16, 'bold'),
            bg='#ffffff'
        ).pack(pady=(30, 10))

        self.decision_var = tk.StringVar(value="NO ACTION NEEDED")
        self.decision_label = tk.Label(
            decision_frame,
            textvariable=self.decision_var,
            font=('Segoe UI', 32, 'bold'),
            bg='#ffffff'
        )
        self.decision_label.pack(pady=20)

        self.confidence_var = tk.StringVar(value="Confidence: 95%")
        confidence_label = tk.Label(
            decision_frame,
            textvariable=self.confidence_var,
            font=('Segoe UI', 14),
            bg='#ffffff',
            fg=self.ibm_secondary
        )
        confidence_label.pack(pady=(0, 20))

        self.reason_var = tk.StringVar(value="Soil moisture optimal, rain unlikely")
        reason_label = tk.Label(
            decision_frame,
            textvariable=self.reason_var,
            font=('Segoe UI', 12),
            bg='#ffffff',
            fg='#666666',
            wraplength=500
        )
        reason_label.pack(pady=(0, 30))

        # Right - Charts Panel
        chart_frame = tk.Frame(content_frame, bg='#ffffff', relief='raised', bd=2)
        chart_frame.pack(side='right', fill='both', expand=True, pady=10)

        tk.Label(
            chart_frame,
            text="📊 7-DAY PERFORMANCE TREND",
            font=('Segoe UI', 14, 'bold'),
            bg='#ffffff'
        ).pack(pady=(20, 10))

        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2, 1, figsize=(8, 6), facecolor='#ffffff'
        )
        plt.tight_layout(pad=3)

        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=20, pady=10)

        # Water Saved Counter
        stats_frame = tk.Frame(self.root, bg=self.ibm_primary)
        stats_frame.pack(fill='x', pady=(10, 0))
        stats_frame.pack_propagate(False)

        self.water_var = tk.StringVar(value="Water Saved: 0 L")
        water_label = tk.Label(
            stats_frame,
            textvariable=self.water_var,
            font=('Segoe UI', 14, 'bold'),
            bg=self.ibm_primary,
            fg=self.ibm_success
        )
        water_label.pack(pady=15)

        # Control buttons
        btn_frame = tk.Frame(self.root, bg=self.ibm_light)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="🔄 New Simulation",
            command=self.new_simulation,
            bg=self.ibm_secondary,
            fg='white',
            font=('Segoe UI', 12, 'bold')
        ).pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="📈 Full Report",
            command=self.show_report,
            bg=self.ibm_primary,
            fg='white',
            font=('Segoe UI', 12, 'bold')
        ).pack(side='left', padx=10)

        # Input widgets for initial values + location
        input_frame = tk.Frame(self.root, bg=self.ibm_light)
        input_frame.pack(pady=(0, 10))

        tk.Label(input_frame, text="Initial Soil Moisture (%)", bg=self.ibm_light).grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.moisture_entry = tk.Entry(input_frame, width=10)
        self.moisture_entry.insert(0, "65")
        self.moisture_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(input_frame, text="Initial Rain Forecast (%)", bg=self.ibm_light).grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.rain_entry = tk.Entry(input_frame, width=10)
        self.rain_entry.insert(0, "10")
        self.rain_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(input_frame, text="Initial Temperature (°C)", bg=self.ibm_light).grid(row=2, column=0, padx=5, pady=2, sticky="e")
        self.temp_entry = tk.Entry(input_frame, width=10)
        self.temp_entry.insert(0, "28")
        self.temp_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(input_frame, text="Location / City", bg=self.ibm_light).grid(row=3, column=0, padx=5, pady=2, sticky="e")
        self.city_entry = tk.Entry(input_frame, width=15)
        self.city_entry.insert(0, "Chennai")
        self.city_entry.grid(row=3, column=1, padx=5, pady=2)

        tk.Button(
            input_frame,
            text="✅ Start Simulation",
            bg=self.ibm_success,
            fg="white",
            command=self.apply_initial_values_and_start
        ).grid(row=4, column=0, columnspan=2, pady=5)

    # ===================== WEATHER API =====================

    def get_temperature_for_city(self, city):
        """
        Uses mock weather data for demonstration (no API key required).
        Replace with real OpenWeather API if you have a valid API key.
        """
        # Mock temperature data for demonstration
        mock_temps = {
            "New York": 15.0,
            "Los Angeles": 22.0,
            "Chicago": 10.0,
            "Houston": 25.0,
            "Phoenix": 28.0,
            "London": 8.0,
            "Tokyo": 12.0,
            "Mumbai": 32.0,
            "Sydney": 20.0,
            "Berlin": 7.0,
            "Chennai": 30.0
        }
        
        # Return mock temperature or random value if city not in list
        if city in mock_temps:
            return mock_temps[city]
        else:
            return random.uniform(15, 30)  # Random temp between 15-30°C

    # ===================== APPLY INITIAL VALUES =====================

    def apply_initial_values_and_start(self):
        city = self.city_entry.get().strip()

        # 1) Temperature from API if city given
        if city:
            temp_from_api = self.get_temperature_for_city(city)
            if temp_from_api is None:
                return  # error already shown
            self.temperature = float(temp_from_api)
            self.temp_entry.delete(0, tk.END)
            self.temp_entry.insert(0, f"{temp_from_api:.1f}")
        else:
            try:
                self.temperature = float(self.temp_entry.get())
            except ValueError:
                messagebox.showerror("Input error", "Please enter a valid temperature or a city name.")
                return

        # 2) Other numeric inputs
        try:
            self.soil_moisture = float(self.moisture_entry.get())
            self.rain_forecast = float(self.rain_entry.get())
        except ValueError:
            messagebox.showerror("Input error", "Please enter valid numeric values.")
            return

        # Optional range checks
        if not (0 <= self.soil_moisture <= 100):
            messagebox.showerror("Input error", "Soil moisture must be between 0 and 100.")
            return
        if not (0 <= self.rain_forecast <= 100):
            messagebox.showerror("Input error", "Rain forecast must be between 0 and 100.")
            return

        self.history = []
        self.water_saved = 0
        self.water_var.set("Water Saved: 0 L")

        # Refresh UI once
        self.refresh_ui()

        # Start simulation only once
        if not self.sim_thread_started:
            self.sim_thread_started = True
            self.start_simulation()

    # ===================== AI DECISION ENGINE =====================

    def ai_decision_engine(self):
        """
        Simple rule-based example:
        - If soil moisture < 40 and rain_prob < 50 -> IRRIGATE
        - If soil moisture > 80 -> STOP IRRIGATION
        - Else -> NO ACTION
        Returns (decision, confidence, reason, water_used, water_saved_increment)
        """
        sm = self.soil_moisture
        rain = self.rain_forecast
        temp = self.temperature

        if sm < 40 and rain < 50:
            decision = "IRRIGATE NOW"
            confidence = 92
            reason = "Soil moisture low and rain unlikely in next 24 hours."
            water_used = 50  # liters (example)
            water_saved_inc = 0
        elif sm > 80:
            decision = "STOP IRRIGATION"
            confidence = 90
            reason = "Soil moisture high; avoid overwatering and root diseases."
            water_used = 0
            water_saved_inc = 20
        else:
            decision = "NO ACTION NEEDED"
            confidence = 88
            reason = "Soil moisture within optimal range for current crop stage."
            water_used = 0
            water_saved_inc = 5

        # Adjust confidence a bit based on temperature:
        if temp > 35 or temp < 15:
            confidence -= 5

        confidence = max(50, min(99, confidence))
        return decision, confidence, reason, water_used, water_saved_inc

    # ===================== SIMULATION LOOP =====================

    def start_simulation(self):
        def worker():
            current_time = datetime.now()
            while self.running:
                # Random small changes to simulate environment
                self.soil_moisture += random.uniform(-2, 2)
                self.soil_moisture = max(0, min(100, self.soil_moisture))

                self.rain_forecast += random.uniform(-5, 5)
                self.rain_forecast = max(0, min(100, self.rain_forecast))

                self.temperature += random.uniform(-0.5, 0.5)

                decision, conf, reason, water_used, water_saved_inc = self.ai_decision_engine()
                self.water_saved += water_saved_inc

                # Update history (for 7 days; here we just simulate timeline)
                self.history.append({
                    "time": current_time,
                    "moisture": self.soil_moisture,
                    "rain": self.rain_forecast,
                    "temp": self.temperature,
                    "decision": decision,
                    "water_saved": self.water_saved
                })
                # Keep last ~7*24 records (if each step is 1 hour; here we just cap length)
                if len(self.history) > 200:
                    self.history.pop(0)

                # Schedule UI update on main thread
                self.root.after(0, self.update_ui_from_sim, decision, conf, reason)

                # Step time
                current_time += timedelta(hours=1)
                time.sleep(1)  # 1 second per step

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def update_ui_from_sim(self, decision, confidence, reason):
        # Update text labels
        self.decision_var.set(decision)
        self.confidence_var.set(f"Confidence: {confidence}%")
        self.reason_var.set(reason)

        # Update sensors
        self.refresh_ui()

    # ===================== UI REFRESH & CHARTS =====================

    def refresh_ui(self):
        # Sensor labels
        self.moisture_var.set(f"{self.soil_moisture:.1f}%")
        self.rain_var.set(f"{self.rain_forecast:.1f}%")
        self.temp_var.set(f"{self.temperature:.1f}°C")

        # Progress bar for moisture
        self.moisture_progress['value'] = self.soil_moisture

        # Water saved label
        self.water_var.set(f"Water Saved: {self.water_saved:.1f} L")

        # Update charts
        self.update_charts()

    def update_charts(self):
        if not self.history:
            return

        times = [h["time"] for h in self.history]
        moisture = [h["moisture"] for h in self.history]
        rain = [h["rain"] for h in self.history]
        water_s = [h["water_saved"] for h in self.history]

        # Clear axes
        self.ax1.clear()
        self.ax2.clear()

        # Top chart: soil moisture & rain
        self.ax1.plot(times, moisture, label="Soil Moisture (%)", color=self.ibm_secondary)
        self.ax1.plot(times, rain, label="Rain Forecast (%)", color=self.ibm_warning)
        self.ax1.set_ylabel("Percent")
        self.ax1.legend(loc="upper left")
        self.ax1.grid(True, alpha=0.3)

        # Bottom chart: water saved
        self.ax2.plot(times, water_s, label="Water Saved (L)", color=self.ibm_success)
        self.ax2.set_ylabel("Liters")
        self.ax2.legend(loc="upper left")
        self.ax2.grid(True, alpha=0.3)

        self.fig.autofmt_xdate()
        self.canvas.draw_idle()

    # ===================== OTHER ACTIONS =====================

    def new_simulation(self):
        # Reset data; user will press Start again
        self.soil_moisture = 65.0
        self.rain_forecast = 10.0
        self.temperature = 28.0
        self.history = []
        self.water_saved = 0
        self.water_var.set("Water Saved: 0 L")

        self.moisture_entry.delete(0, tk.END)
        self.moisture_entry.insert(0, "65")
        self.rain_entry.delete(0, tk.END)
        self.rain_entry.insert(0, "10")
        self.temp_entry.delete(0, tk.END)
        self.temp_entry.insert(0, "28")

        self.refresh_ui()

    def show_report(self):
        # Simple popup summary; you can expand this
        msg = f"Records in history: {len(self.history)}\nTotal water saved: {self.water_saved:.1f} L"
        messagebox.showinfo("Full Report", msg)

    def on_close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
        root = tk.Tk()
        app = IBMAgriculturalAdvisor(root)
        root.mainloop()
