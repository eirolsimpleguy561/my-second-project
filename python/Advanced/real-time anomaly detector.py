import numpy as np
import pandas as pd
from collections import deque
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import random
import time
from sklearn.ensemble import IsolationForest

class StatisticalDetector:
    """Statistical anomaly detection methods"""
    
    @staticmethod
    def z_score(data: List[float], threshold: float = 3.0) -> List[int]:
        """Detect anomalies using Z-score"""
        if len(data) < 3:
            return [0] * len(data)
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return [0] * len(data)
        
        z_scores = [(x - mean) / std for x in data]
        return [1 if abs(z) > threshold else 0 for z in z_scores]
    
    @staticmethod
    def iqr(data: List[float]) -> List[int]:
        """Detect anomalies using Interquartile Range"""
        if len(data) < 4:
            return [0] * len(data)
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return [1 if x < lower_bound or x > upper_bound else 0 for x in data]
    
    @staticmethod
    def moving_average(data: List[float], window: int = 10, threshold: float = 2.0) -> List[int]:
        """Detect anomalies using moving average"""
        if len(data) < window:
            return [0] * len(data)
        
        anomalies = []
        for i in range(len(data)):
            if i < window:
                anomalies.append(0)
                continue
            
            window_data = data[i-window:i]
            mean = np.mean(window_data)
            std = np.std(window_data)
            
            if std == 0:
                anomalies.append(0)
            else:
                z = (data[i] - mean) / std
                anomalies.append(1 if abs(z) > threshold else 0)
        
        return anomalies

class MLDetector:
    """Machine learning-based anomaly detection"""
    
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False
        self.training_data = []
    
    def add_training_data(self, data: List[float]):
        """Add data to training set"""
        self.training_data.extend(data)
        if len(self.training_data) > 100:
            self._train()
    
    def _train(self):
        """Train the Isolation Forest model"""
        if len(self.training_data) < 50:
            return
        
        # Convert to 2D array
        X = np.array(self.training_data).reshape(-1, 1)
        self.model.fit(X)
        self.is_trained = True
    
    def predict(self, data: List[float]) -> List[int]:
        """Predict anomalies"""
        if not self.is_trained:
            return [0] * len(data)
        
        X = np.array(data).reshape(-1, 1)
        predictions = self.model.predict(X)
        # Isolation Forest returns -1 for anomalies, 1 for normal
        return [1 if pred == -1 else 0 for pred in predictions]

class AnomalyDetector:
    """Main anomaly detection system"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_window = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.anomaly_history = deque(maxlen=1000)
        
        # Detectors
        self.stat_detector = StatisticalDetector()
        self.ml_detector = MLDetector()
        
        # Configuration
        self.method = 'ensemble'  # 'statistical', 'ml', 'ensemble'
        self.z_threshold = 3.0
        self.moving_window = 10
        self.alert_callbacks = []
        
        # Statistics
        self.total_detected = 0
        self.last_alert_time = 0
        self.alert_cooldown = 5  # seconds
    
    def add_data_point(self, value: float, timestamp: Optional[float] = None):
        """Add a new data point for analysis"""
        if timestamp is None:
            timestamp = time.time()
        
        self.data_window.append(value)
        self.timestamps.append(timestamp)
        
        # Check for anomalies
        anomaly = self._detect_anomaly(value)
        
        if anomaly:
            self.total_detected += 1
            self.anomaly_history.append({
                'timestamp': timestamp,
                'value': value,
                'method': self.method
            })
            
            # Trigger alerts
            self._trigger_alerts(value, timestamp)
        
        return anomaly
    
    def _detect_anomaly(self, value: float) -> bool:
        """Detect if a value is anomalous"""
        if len(self.data_window) < 3:
            return False
        
        data_list = list(self.data_window)
        
        if self.method == 'statistical':
            # Use Z-score
            z_scores = self.stat_detector.z_score(data_list, self.z_threshold)
            return bool(z_scores[-1])
        
        elif self.method == 'ml':
            # Use ML detector
            self.ml_detector.add_training_data(data_list[:-1])
            predictions = self.ml_detector.predict([value])
            return bool(predictions[0])
        
        else:  # ensemble
            # Combine multiple methods
            z_scores = self.stat_detector.z_score(data_list, self.z_threshold)
            iqr_results = self.stat_detector.iqr(data_list)
            ma_results = self.stat_detector.moving_average(data_list, self.moving_window)
            
            # ML detection
            self.ml_detector.add_training_data(data_list[:-1])
            ml_predictions = self.ml_detector.predict([value])
            
            # Vote: at least 2 methods agree
            votes = [
                bool(z_scores[-1]),
                bool(iqr_results[-1]),
                bool(ma_results[-1]),
                bool(ml_predictions[0])
            ]
            
            return sum(votes) >= 2
    
    def _trigger_alerts(self, value: float, timestamp: float):
        """Trigger alerts for anomalies"""
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        self.last_alert_time = current_time
        
        alert = {
            'timestamp': timestamp,
            'value': value,
            'method': self.method,
            'threshold': self.z_threshold,
            'window_size': len(self.data_window)
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def register_alert_callback(self, callback):
        """Register callback for anomaly alerts"""
        self.alert_callbacks.append(callback)
    
    def get_stats(self) -> dict:
        """Get detection statistics"""
        return {
            'total_points': len(self.data_window),
            'total_anomalies': self.total_detected,
            'anomaly_rate': self.total_detected / max(1, len(self.data_window)),
            'recent_anomalies': list(self.anomaly_history)[-10:],
            'method': self.method,
            'window_size': self.window_size
        }
    
    def set_method(self, method: str):
        """Set detection method"""
        if method in ['statistical', 'ml', 'ensemble']:
            self.method = method
    
    def set_threshold(self, threshold: float):
        """Set Z-score threshold"""
        self.z_threshold = threshold

class DataStreamSimulator:
    """Simulate real-time data stream"""
    
    def __init__(self, pattern: str = 'normal'):
        self.pattern = pattern
        self.seasonal_step = 0
    
    def generate_value(self) -> float:
        """Generate a data point with potential anomalies"""
        if self.pattern == 'normal':
            # Normal distribution with occasional spikes
            value = random.gauss(100, 10)
            # Random spikes
            if random.random() < 0.02:  # 2% chance of anomaly
                value += random.choice([-50, 50, 80, -80])
            return value
        
        elif self.pattern == 'seasonal':
            # Seasonal pattern with trend
            self.seasonal_step += 0.1
            season = 20 * np.sin(self.seasonal_step)
            trend = self.seasonal_step * 0.5
            noise = random.gauss(0, 5)
            value = 100 + season + trend + noise
            
            # Add anomalies
            if random.random() < 0.03:
                value += random.choice([-60, 60, 100])
            return value
        
        elif self.pattern == 'multivariate':
            # Correlated series
            base = random.gauss(100, 10)
            correlation = 0.3
            value = base * (1 - correlation) + random.gauss(100, 10) * correlation
            
            if random.random() < 0.02:
                value *= random.choice([0.5, 1.5, 2.0])
            return value
        
        else:
            return random.gauss(100, 10)

def alert_printer(alert: dict):
    """Example alert callback"""
    timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
    print(f"🚨 ANOMALY DETECTED [{timestamp}]: value={alert['value']:.2f}, "
          f"method={alert['method']}, threshold={alert['threshold']}")

async def main():
    print("=== Real-time Anomaly Detector ===")
    
    # Create detector
    detector = AnomalyDetector(window_size=100)
    detector.register_alert_callback(alert_printer)
    
    # Choose pattern
    patterns = ['normal', 'seasonal', 'multivariate']
    pattern = input(f"Choose data pattern {patterns}: ").strip() or 'normal'
    
    # Choose method
    methods = ['statistical', 'ml', 'ensemble']
    method = input(f"Choose detection method {methods}: ").strip() or 'ensemble'
    detector.set_method(method)
    
    print(f"\nStarting data stream with {pattern} pattern using {method} detection")
    print("Press Ctrl+C to stop")
    
    # Create simulator
    simulator = DataStreamSimulator(pattern)
    
    # Run simulation
    try:
        while True:
            # Generate data
            value = simulator.generate_value()
            
            # Detect anomalies
            is_anomaly = detector.add_data_point(value)
            
            # Print status
            if is_anomaly:
                print(f"⚠️  Anomaly: {value:.2f}", end="")
                
                # Print recent stats
                stats = detector.get_stats()
                print(f" (Rate: {stats['anomaly_rate']:.2%})")
            
            # Print periodic stats
            if len(detector.data_window) % 50 == 0:
                stats = detector.get_stats()
                print(f"\n📊 Stats: {stats['total_points']} points, "
                      f"{stats['total_anomalies']} anomalies, "
                      f"rate: {stats['anomaly_rate']:.2%}")
            
            await asyncio.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\nGenerating final report...")
        
        # Show final statistics
        stats = detector.get_stats()
        print(f"\n=== Final Report ===")
        print(f"Total points analyzed: {stats['total_points']}")
        print(f"Total anomalies detected: {stats['total_anomalies']}")
        print(f"Anomaly rate: {stats['anomaly_rate']:.2%}")
        print(f"Detection method: {stats['method']}")
        
        # Show recent anomalies
        if stats['recent_anomalies']:
            print(f"\nRecent anomalies:")
            for anomaly in stats['recent_anomalies'][-5:]:
                timestamp = datetime.fromtimestamp(anomaly['timestamp']).strftime('%H:%M:%S')
                print(f"  {timestamp}: {anomaly['value']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())

# Install: pip install numpy pandas scikit-learn