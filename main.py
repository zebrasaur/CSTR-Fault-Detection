# list (ordered collection)
readings = [23.4, 25.1, 22.8, 26.0, 24.5]
readings.append(27.2)

#dictionary (key-value mapping)
asset = {
    "id": "A-104",
    "location": "North Wing",
    "status": "Active",
    "load_capacity": 5000
}
# iteration
print("--- Sensor Readings ---")
for val in readings:
    status = "HIGH" if val > 25.0 else "NORMAL"
    print(f"value: {val} C | Status: {status}")

print("\n-- Asset Specs --")
for key, value in asset.items():
    print(f"{key.replace('_', '').title()}: {value}")