from typing import List, Dict, Tuple, Union
from datetime import datetime

class Vehicle:
    def __init__(self, 
                 registration_number: str, 
                 gps_coordinates: Union[Tuple[float, float], Dict[str, float]], 
                 speed: float, 
                 last_update_timestamp: Union[str, datetime], 
                 origin: str, 
                 destination: str, 
                 business_unit: str, 
                 status: str):
        self.registration_number = registration_number
        self.gps_coordinates = gps_coordinates
        self.speed = speed
        self.last_update_timestamp = last_update_timestamp
        self.origin = origin
        self.destination = destination
        self.business_unit = business_unit
        self.status = status

class Shipment:
    def __init__(self, 
                 vehicle_registration_number: str, 
                 sku_details: List[Dict[str, Union[str, int]]], 
                 scheduled_arrival_time: Union[str, datetime], 
                 destination_warehouse_id: str):
        self.vehicle_registration_number = vehicle_registration_number
        self.sku_details = sku_details
        self.scheduled_arrival_time = scheduled_arrival_time
        self.destination_warehouse_id = destination_warehouse_id

class Warehouse:
    def __init__(self, 
                 warehouse_id: str, 
                 name: str, 
                 location_coordinates: Union[Tuple[float, float], Dict[str, float]], 
                 geofence_radius_km: float):
        self.warehouse_id = warehouse_id
        self.name = name
        self.location_coordinates = location_coordinates
        self.geofence_radius_km = geofence_radius_km
