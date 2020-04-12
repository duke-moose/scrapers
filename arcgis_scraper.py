from datetime import datetime
import json
import pandas as pd
import requests
import os


class ArcGisServerScraper:
    def __init__(self, gis_dict):
        self.url = gis_dict['arcgis_url']
        self.save_path = gis_dict['save_dir_path']
        self.save_dir = os.path.join(
            self.save_path,
            gis_dict['save_file_base_name']
        )
        self.max_record_query = gis_dict['max_record_query']
        self.file_type = gis_dict['output_type']
        self.where = gis_dict['where']

    def request_check(self, res):
        print('URL:: ', self.url)
        print('Body:: ', res.request.body)
        print('Headers:: ', res.request.headers)
        print('Status:: ', res.status_code)

    def get_arc_gis_request(self, objectids=None):
        arc_gis_data = {
            'where': self.where,
            'objectIds': objectids,
            'outFields': '*',
            'f': 'p' + self.file_type,
        }
        response = requests.post(self.url, data=arc_gis_data)
        self.request_check(response) # Log the response to track
        return response.content

    def make_save_file(self, min_number=None, max_number=None):
        if max_number:
            id_range = '{}-{}'.format(
                str(min_number),
                str(max_number),
            )
        else:
            id_range = None
        gis_save_file = '{}_{}_{}.{}'.format(
                self.save_dir,
                "" if id_range is None else id_range,
                datetime.now().strftime('%Y-%m-%d'),
                self.file_type,
        )
        return gis_save_file

    def run_json_grabber(self):
        chunk = int(self.max_record_query * 0.75)  # Request chunks in sizes less than GIS Server record limit.
        ids_list = [0]  # First ObjectId to find.
        end_range = chunk
        while True:
            ids_list = [num for num in range(max(ids_list)+1, end_range)]
            end_range += chunk
            gis_data = self.get_arc_gis_request(objectids=ids_list)
            if self.file_type in ['json', 'geojson']:
                pass
                gis_data = json.loads(gis_data)
                # # Find maximum Ids for check to Stop code
                range_max = max(ids_list)
                gis_data_max = gis_data['features'][-1]['attributes']['OBJECTID']
                print('Search range max: {}, ObjectId max: {}'.format(range_max, gis_data_max))
                # Save output
                gis_save_file = self.make_save_file(min(ids_list), gis_data_max)
                with open(gis_save_file, 'w') as infile:
                    json.dump(gis_data, infile, ensure_ascii=False, indent=4)
            else:
                print(self.file_type + ' not yet supported')
                break

            if range_max > gis_data_max:
                print("Search Range max exceeds Maximum ObjectId")
                break

    def save_all_json_to_csv(self):
        print('Opening JSON files and saving Features to CSV')
        file_ext = 'json'
        # Create list of all files with given extension
        list_of_ext_files = []
        for root, dirs, files in os.walk(self.save_path):
            for file in files:
                if file.endswith(file_ext):
                    list_of_ext_files.append(os.path.join(root, file))

        # Open each files and save to single dataframe
        df = pd.DataFrame()
        for file_path in list_of_ext_files:
            with open(file_path, 'r') as infile:
                jf = json.load(infile)
            arcgis_features = [jf['features'][num]['attributes'] for num in range(0, len(jf['features']))]
            df = pd.concat([df, pd.DataFrame.from_dict(arcgis_features)], ignore_index=True)
        df = df.sort_values(by='OBJECTID', ascending=True) # Sort dict by values from OBJECTID
        df.to_csv('{}_{}.csv'.format(self.save_dir, datetime.now().strftime('%Y-%m-%d')))


if __name__ == "__main__":
    arcgis_setup = {
        'arcgis_url': ('https://services.arcgis.com/DO4gTjwJVIJ7O9Ca/ArcGIS/rest/services/'
                       'Unacast_Latest_Available__Visitation_and_Distance_/FeatureServer/0/query?'),
        'save_dir_path': os.path.join(os.getcwd(), 'covid_data'),
        'save_file_base_name': 'unacast_objid',
        'where': None,  # '1=1' if you can grab all records at once.
        'max_record_query': 2000,  # None if there is no maximum query number.
        'output_type': 'json'
    }
    arcgis = ArcGisServerScraper(arcgis_setup)
    arcgis.run_json_grabber()
    print('='*50)
    ans = input('\nCreate CSV from files? (y/n):')
    if ans.lower() == 'y':
        print('Creating CSV file.')
        arcgis.save_all_json_to_csv()
    else:
        print('No CSV file created.')