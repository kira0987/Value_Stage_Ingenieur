import requests
import os
import re

def sanitize_filename(name):
    return re.sub(r'[^\w\-\.]', '_', name)

api_url = "https://catalog.data.gov.tn/fr/api/3/action/package_search"
save_folder = "downloaded_data"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

params = {'q': '*:*', 'rows': 0}
response = requests.get(api_url, params=params)
if response.status_code == 200:
    data = response.json()
    total = data['result']['count']
    print(f"Total datasets: {total}")
else:
    print("Failed to fetch total count")
    exit()

batch_size = 100
num_batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

for i in range(num_batches):
    start = i * batch_size
    params = {'q': '*:*', 'rows': batch_size, 'start': start}
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        datasets = data['result']['results']
        for dataset in datasets:
            dataset_name = sanitize_filename(dataset['name'])
            dataset_folder = os.path.join(save_folder, dataset_name)
            if not os.path.exists(dataset_folder):
                os.makedirs(dataset_folder)
            for resource in dataset.get('resources', []):
                if resource['format'].upper() in ['CSV', 'XLSX']:
                    resource_name = sanitize_filename(resource.get('name', 'resource'))
                    file_extension = resource['format'].lower()
                    file_name = f"{resource_name}.{file_extension}"
                    file_path = os.path.join(dataset_folder, file_name)
                    try:
                        file_response = requests.get(resource['url'])
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)
                        print(f"Downloaded {file_name} to {file_path}")
                    except Exception as e:
                        print(f"Failed to download {resource['url']}: {e}")
    else:
        print(f"Failed to fetch batch starting from {start}")
        break

print("All datasets have been processed, and XLSX/CSV files have been downloaded.")