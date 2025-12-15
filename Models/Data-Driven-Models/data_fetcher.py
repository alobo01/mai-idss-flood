"""
Data Fetcher Module
Automatically fetches data from USGS and weather APIs using actual production methods
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DataFetcher:
    """
    Fetches real-time data from USGS and weather APIs
    """
    
    def __init__(self):
        # USGS station IDs with coordinates
        self.stations = {
            'target': {
                'id': '07010000',
                'name': 'Mississippi River at St. Louis, MO',
                'lat': 38.6270,
                'lon': -90.1994
            },
            'hermann': {
                'id': '06934500',
                'name': 'Missouri River at Hermann, MO',
                'lat': 38.7098,
                'lon': -91.4385
            },
            'grafton': {
                'id': '05587450',
                'name': 'Mississippi River at Grafton, IL',
                'lat': 38.9680,
                'lon': -90.4290
            },
        }
        
        # Coordinates for St. Louis (for weather data)
        self.weather_lat = 38.6270
        self.weather_lon = -90.1994
        
        print(f"📍 Data Sources:")
        for key, station in self.stations.items():
            print(f"   {station['name']} ({station['id']})")
    
    def fetch_last_30_days(self):
        """
        Fetch all required data for the last 30 days
        
        Returns:
            DataFrame with all features needed for prediction
        """
        
        print("\n📡 Fetching live data from APIs...")
        
        # Date range (need 35 days to compute 30-day precipitation windows)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=35)
        str_start = start_date.strftime("%Y-%m-%d")
        str_end = end_date.strftime("%Y-%m-%d")
        
        # Fetch weather data
        print("\n  [1/2] Fetching weather data...")
        weather_data = self._fetch_weather_data(str_start, str_end)
        
        # Fetch river levels
        print("\n  [2/2] Fetching USGS river data...")
        river_data = self._fetch_usgs_data()
        
        # Merge datasets
        print("\n  [3/3] Merging datasets...")
        combined = self._merge_data(river_data, weather_data)
        
        # Keep only last 30 days for prediction
        combined = combined.tail(30).reset_index(drop=True)
        
        print(f"\n  ✓ Final dataset: {len(combined)} days")
        
        return combined
    
    def _fetch_weather_data(self, str_start, str_end):
        """
        Fetch weather data from Open-Meteo API
        """
        
        print(f"    ☁️  Open-Meteo API ({self.weather_lat}, {self.weather_lon})...")
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": self.weather_lat,
            "longitude": self.weather_lon,
            "start_date": str_start,
            "end_date": str_end,
            "daily": [
                "precipitation_sum",
                "temperature_2m_mean",
                "snowfall_sum",
                "relative_humidity_2m_mean",
                "wind_speed_10m_mean",
                "soil_moisture_28_to_100cm_mean"
            ],
            "timezone": "UTC"
        }
        
        try:
            response = requests.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            daily = data['daily']
            
            df = pd.DataFrame({
                'date': pd.to_datetime(daily['time']),
                'daily_precip': daily['precipitation_sum'],
                'daily_temp_avg': daily['temperature_2m_mean'],
                'daily_snowfall': daily['snowfall_sum'],
                'daily_humidity': daily['relative_humidity_2m_mean'],
                'daily_wind': daily['wind_speed_10m_mean'],
                'soil_deep_30d': daily['soil_moisture_28_to_100cm_mean'],
            })
            
            # Fill missing soil moisture with reasonable default
            df['soil_deep_30d'] = df['soil_deep_30d'].fillna(0.35)
            
            print(f"      ✓ Retrieved {len(df)} days")
            return df
            
        except Exception as e:
            # No fabricated data; surface the failure
            raise RuntimeError(f"Weather API failed: {e}")
    
    def _fetch_usgs_data(self):
        """
        Fetch river levels from USGS using INSTANTANEOUS VALUES (15-min data)
        Then resample to daily means
        """
        
        dfs_river = []
        
        for key, station in self.stations.items():
            site_id = station['id']
            site_name = station['name']
            
            print(f"    🌊 {site_name} ({site_id})...")
            
            try:
                # USGS Instantaneous Values API
                url = "https://waterservices.usgs.gov/nwis/iv/"
                params = {
                    'format': 'json',
                    'sites': site_id,
                    'period': 'P35D',  # Last 35 days (to get enough for 30-day windows)
                    'parameterCd': '00065'  # Gage height in feet
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Parse response
                if 'value' in data and 'timeSeries' in data['value'] and data['value']['timeSeries']:
                    vals_list = data['value']['timeSeries'][0]['values'][0]['value']
                    
                    if vals_list:
                        # Load 15-minute data
                        temp_df = pd.DataFrame(vals_list)
                        temp_df['value'] = pd.to_numeric(temp_df['value'], errors='coerce')
                        temp_df['dateTime'] = pd.to_datetime(temp_df['dateTime']).dt.tz_localize(None)
                        
                        # Resample to daily mean (matches training data)
                        temp_df['date'] = temp_df['dateTime'].dt.floor('D')
                        daily_mean = temp_df.groupby('date')['value'].mean().reset_index()
                        
                        # Store with correct column name
                        df_station = pd.DataFrame({
                            'date': daily_mean['date'],
                            f'{key}_level': daily_mean['value']
                        })
                        
                        dfs_river.append(df_station)
                        print(f"      ✓ Retrieved {len(daily_mean)} daily averages")
                    else:
                        print(f"      ⚠️  Data list is empty")
                        raise ValueError("Empty data")
                else:
                    print(f"      ⚠️  No timeSeries found")
                    raise ValueError("No timeSeries")
                    
            except Exception as e:
                raise RuntimeError(f"USGS fetch failed for {site_id}: {e}")
            
            time.sleep(1)  # Be nice to USGS API
        
        # Merge all stations
        result = dfs_river[0]
        for df in dfs_river[1:]:
            result = result.merge(df, on='date', how='outer')
        
        return result
    
    def _merge_data(self, river_data, weather_data):
        """
        Merge river and weather data into final format
        """
        
        # Ensure both have date as datetime
        river_data['date'] = pd.to_datetime(river_data['date'])
        weather_data['date'] = pd.to_datetime(weather_data['date'])
        
        # Merge (left join on weather to keep all weather dates)
        combined = weather_data.merge(river_data, on='date', how='left')
        
        # Rename target column to match training data
        combined = combined.rename(columns={'target_level': 'target_level_max'})
        
        # Sort by date
        combined = combined.sort_values('date').reset_index(drop=True)
        
        # Fill missing values (forward fill then backward fill)
        combined = combined.ffill().bfill()
        
        return combined
    
    def visualize_stations(self):
        """
        Print station information
        """
        print("\n" + "="*70)
        print("STATION MAP")
        print("="*70)
        
        for key, station in self.stations.items():
            print(f"\n📍 {station['name']}")
            print(f"   ID:  {station['id']}")
            print(f"   Lat: {station['lat']:.4f}")
            print(f"   Lon: {station['lon']:.4f}")


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def get_latest_data():
    """
    Convenience function to quickly fetch latest data
    
    Returns:
        DataFrame with 30 days of data ready for prediction
    """
    fetcher = DataFetcher()
    return fetcher.fetch_last_30_days()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TESTING DATA FETCHER")
    print("="*70)
    
    fetcher = DataFetcher()
    fetcher.visualize_stations()
    
    print("\n" + "="*70)
    print("FETCHING DATA")
    print("="*70)
    
    data = fetcher.fetch_last_30_days()
    
    print("\n" + "="*70)
    print("SAMPLE DATA (last 5 days)")
    print("="*70)
    print(data[['date', 'target_level_max', 'hermann_level', 'grafton_level', 
                'daily_precip', 'daily_temp_avg']].tail(5))
    
    print("\n✅ Data fetcher test complete!")
