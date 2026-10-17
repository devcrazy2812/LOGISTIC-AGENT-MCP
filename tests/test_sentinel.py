import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.sentinel_agent import SentinelAgent
from src.models.entities import Vehicle, Order, Disruption


class TestSentinelSignals(unittest.TestCase):
    def test_01_cold_chain_nominal_and_excursion(self):
        agent = SentinelAgent()
        v = Vehicle(
            id="V-04",
            name="PolarExpress (Reefer)",
            type="reefer_truck",
            fuel_type="Diesel",
            capacity_kg=2000.0,
            capacity_volume_m3=12.0,
            cost_per_km=1.8,
            co2_per_km_kg=0.45,
            avg_speed_kmh=45.0,
            depot_id="DEPOT-03",
            current_lat=37.78,
            current_lng=-122.40,
            status="en_route",
            assigned_orders=["ORD-03"]
        )
        o = Order(
            id="ORD-03",
            customer="St. Jude Hospital",
            item="cold_chain_vaccines",
            quantity=100,
            weight_kg=80.0,
            volume_m3=0.8,
            lat=37.785,
            lng=-122.405,
            priority="CRITICAL",
            deadline_minutes=90,
            sla_penalty_usd=5000.0,
            status="assigned"
        )

        # In nominal status: no excursion alert
        alerts = agent.scan_cold_chain_telematics([v], [o])
        self.assertEqual(len(alerts), 0)

        # In disrupted status: excursion alert generated
        v.status = "disrupted"
        alerts = agent.scan_cold_chain_telematics([v], [o])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], "COLD_CHAIN_EXCURSION")
        self.assertGreater(alerts[0]["temperature_celsius"], 8.0)

    def test_02_weather_radar_signals(self):
        agent = SentinelAgent()
        coords = [
            (37.772, -122.418),  # In storm front zone
            (37.338, -121.886)   # Outside zone
        ]
        alerts = agent.check_weather_signals(coords)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], "STORM_FRONT")
        self.assertIn("Flash flood", alerts[0]["advisory"])


if __name__ == "__main__":
    unittest.main()
