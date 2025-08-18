#!/usr/bin/env python3
"""
Load test script for DSG Telemetry Service.
Tests the performance envelope of 1k messages per second for 60 seconds.
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import List

import httpx


class LoadTester:
    """Load tester for telemetry ingestion."""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "start_time": None,
            "end_time": None,
        }
    
    def generate_telemetry_data(self, auv_id: str = "AUV-003") -> dict:
        """Generate sample telemetry data."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Generate realistic position data
        lat = random.uniform(-15.0, -14.0)
        lng = random.uniform(-126.0, -125.0)
        
        # Generate environmental data with some variation
        sediment = random.uniform(10.0, 30.0)  # Some values will trigger alerts
        dissolved_oxygen = random.uniform(5.0, 8.0)  # Some values will trigger alerts
        battery_level = random.randint(20, 50)  # Some values will trigger alerts
        
        return {
            "timestamp": timestamp,
            "auv_id": auv_id,
            "position": {
                "lat": lat,
                "lng": lng,
                "depth": random.randint(3000, 3500),
                "speed": random.uniform(0.5, 2.0),
                "heading": random.randint(0, 360),
            },
            "env": {
                "turbidity_ntu": random.uniform(5.0, 20.0),
                "sediment_mg_l": sediment,
                "dissolved_oxygen_mg_l": dissolved_oxygen,
                "temperature_c": random.uniform(3.0, 6.0),
            },
            "plume": {
                "concentration_mg_l": random.uniform(40.0, 60.0),
            },
            "species_detections": [
                {
                    "name": random.choice([
                        "Benthic Octopod",
                        "Deep Sea Coral",
                        "Abyssal Fish",
                        "Sea Cucumber",
                    ]),
                    "distance_m": random.uniform(50.0, 200.0),
                }
            ] if random.random() < 0.3 else [],  # 30% chance of species detection
            "battery": {
                "level_pct": battery_level,
                "voltage_v": random.uniform(40.0, 48.0),
            },
        }
    
    async def send_telemetry(self, client: httpx.AsyncClient, data: dict) -> bool:
        """Send a single telemetry record."""
        try:
            response = await client.post(
                f"{self.base_url}/api/telemetry/ingest",
                json=data,
                headers=self.headers,
                timeout=10.0,
            )
            
            if response.status_code == 201:
                return True
            else:
                print(f"Failed to send telemetry: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending telemetry: {e}")
            return False
    
    async def run_load_test(self, messages_per_second: int = 1000, duration_seconds: int = 60):
        """Run the load test."""
        print(f"🚀 Starting load test: {messages_per_second} msg/s for {duration_seconds} seconds")
        print(f"📊 Target: {messages_per_second * duration_seconds} total messages")
        
        self.stats["start_time"] = time.time()
        
        # Calculate timing
        delay = 1.0 / messages_per_second
        total_messages = messages_per_second * duration_seconds
        
        # Create HTTP client with connection pooling
        limits = httpx.Limits(max_keepalive_connections=100, max_connections=100)
        async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
            tasks = []
            start_time = time.time()
            
            for i in range(total_messages):
                # Generate telemetry data
                data = self.generate_telemetry_data()
                
                # Create task for sending telemetry
                task = asyncio.create_task(self.send_telemetry(client, data))
                tasks.append(task)
                
                # Add small delay to spread requests
                if i % 100 == 0 and i > 0:
                    await asyncio.sleep(0.01)  # Small delay every 100 requests
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                self.stats["total_requests"] += 1
                if result is True:
                    self.stats["successful_requests"] += 1
                else:
                    self.stats["failed_requests"] += 1
        
        self.stats["end_time"] = time.time()
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results."""
        duration = self.stats["end_time"] - self.stats["start_time"]
        success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
        actual_rate = self.stats["total_requests"] / duration
        
        print("\n" + "="*60)
        print("📈 LOAD TEST RESULTS")
        print("="*60)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Total Requests: {self.stats['total_requests']}")
        print(f"✅ Successful: {self.stats['successful_requests']}")
        print(f"❌ Failed: {self.stats['failed_requests']}")
        print(f"📈 Success Rate: {success_rate:.2f}%")
        print(f"🚀 Actual Rate: {actual_rate:.2f} requests/second")
        print("="*60)
        
        if success_rate >= 99.0:
            print("🎉 SUCCESS: Load test passed!")
        else:
            print("⚠️  WARNING: Some requests failed")


async def check_server_ready(base_url: str) -> bool:
    """Check if the server is ready."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/health/healthz", timeout=5.0)
            return response.status_code == 200
    except Exception:
        return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test for DSG Telemetry Service")
    parser.add_argument("--url", default="http://localhost:8000", help="Service URL")
    parser.add_argument("--token", default="your-auth-token", help="Authentication token")
    parser.add_argument("--rate", type=int, default=1000, help="Messages per second")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    # Check if server is ready
    print("🔍 Checking if server is ready...")
    if not await check_server_ready(args.url):
        print("❌ Server is not ready. Please start the service first.")
        return
    
    print("✅ Server is ready!")
    
    # Run load test
    tester = LoadTester(args.url, args.token)
    await tester.run_load_test(args.rate, args.duration)


if __name__ == "__main__":
    asyncio.run(main())
