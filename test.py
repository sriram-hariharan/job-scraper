from src.discovery.greenhouse_discovery import discover_greenhouse_from_api

companies = discover_greenhouse_from_api()

print("Total greenhouse discovered:", len(companies))