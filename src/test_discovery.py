from discovery.domain_ats_discovery import discover_from_domains
from discovery.save_companies import save_companies

gh, ashby, lever = discover_from_domains()

save_companies(gh, "data/greenhouse_companies.txt")
save_companies(ashby, "data/ashby_companies.txt")
save_companies(lever, "data/lever_companies.txt")

print("Greenhouse discovered:", gh)
print("Ashby discovered:", ashby)
print("Lever discovered:", lever)