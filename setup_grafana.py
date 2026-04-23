import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
AUTH = ('admin', 'admin')

# Wait for Grafana to be ready
for _ in range(10):
    try:
        r = requests.get(f"{GRAFANA_URL}/api/health")
        if r.status_code == 200:
            break
    except:
        pass
    time.sleep(2)

# Change password from admin to admin (it asks to change on first login)
requests.put(f"{GRAFANA_URL}/api/user/password", json={"oldPassword": "admin", "newPassword": "admin", "confirmNew": "admin"}, auth=AUTH)

# Add MySQL data source
ds_payload = {
    "name": "MySQL",
    "type": "mysql",
    "url": "host.docker.internal:3306", # Assumes Windows/Mac Docker to reach host localhost where mysql is mapped, but wait, both are in docker.
    # It's better to use host.docker.internal to reach the host's forwarded 3306 port.
    "access": "proxy",
    "user": "root",
    "database": "tweet_monitoring",
    "secureJsonData": {
        "password": "0000"
    }
}
r_ds = requests.post(f"{GRAFANA_URL}/api/datasources", json=ds_payload, auth=AUTH)
print("Data Source:", r_ds.status_code, r_ds.text)

# Read dashboard JSON
with open('Twitter_Bulk_Analysis/grafana_dashboard_twitter_bulk.json', 'r') as f:
    dashboard_data = json.load(f)

# The exported dashboard might have a 'id' field, which should be null for a new one
dashboard_data['id'] = None

dashboard_payload = {
    "dashboard": dashboard_data,
    "overwrite": True
}
r_dash = requests.post(f"{GRAFANA_URL}/api/dashboards/db", json=dashboard_payload, auth=AUTH)
print("Dashboard:", r_dash.status_code, r_dash.text)
