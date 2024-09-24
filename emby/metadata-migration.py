from plexapi.myplex import MyPlexAccount
import json
import argparse
import requests
from urllib.parse import urlencode
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

VERIFY_SSL = False

PLEX_URL = "http://192.168.1.3:32400/"
PLEX_TOKEN = "x7SE3-iQNwV-WiQQmrM4"
PLEX_SERVER_NAME = "Home"
PLEX_MOVIE_LIBRARIES = "Movies"
PLEX_SERIES_LIBRARIES = "TV Shows"
EMBY_URL = "http://192.168.1.3:8096/emby/"
EMBY_APIKEY = "1f33e7ffd8ed43e2b3ed69b41c4b39dc"

## The emby user ID can be for any user on your server but it should be one that has access to all the media.
EMBY_USERNAME = "Matt_Simoni"


# ----------------- [Do not edit below this line] ----------------- 

class emby:
    def __init__(self, url, apikey, verify_ssl=False, debug=None):
        self.url = url
        self.apikey = apikey
        self.debug = debug

        self.session = Session()
        self.adapters = HTTPAdapter(max_retries=3,
                                    pool_connections=1,
                                    pool_maxsize=1,
                                    pool_block=True)
        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)

        # Ignore verifying the SSL certificate
        if verify_ssl is False:
            self.session.verify = False
            # Disable the warning that the request is insecure, we know that...
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _call_api(self, cmd, method='GET', payload=None, data=None):
        params = (
            ('api_key', self.apikey),
        )

        if payload:
            params = params + payload

        headers = {
            'accept': '',
            'Content-Type': 'application/json',
        }

        if method == 'GET':
            try:
                response = requests.get(self.url + cmd, headers=headers, params=params, data=data)
            except RequestException as e:
                print("EMBY request failed for cmd '{}'. Invalid EMBY URL? Error: {}".format(cmd, e))
        elif method == 'POST':
            try:
                response = requests.post(self.url + cmd, headers=headers, params=params, data=data)
            except RequestException as e:
                print("EMBY request failed for cmd '{}'. Invalid EMBY URL? Error: {}".format(cmd, e))
        if response.status_code != 204:
            try:
                response_json = json.loads(response.text)
            except ValueError:
                print(
                    "Failed to parse json response for Emby API cmd '{}': {}"
                    .format(cmd, response.content))
                return
        if response.status_code == 200:
            if self.debug:
                print("Successfully called Emby API cmd '{}'".format(cmd))
            return response_json
        elif response.status_code == 204:
            if self.debug:
                print("Successfully called Emby API cmd '{}'".format(cmd))
        else:
            error_msg = response.reason
            print("Emby API cmd '{}' failed: {}".format(cmd, error_msg))
            return
            
    def get_emby_item(self, itemId, userID):
        path = f"/Users/{userID }/Items/{itemId}?"
        params = {"Recursive": "true"}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_movies(self):
        path = f"/Items?"
        params = {"Recursive": "true", "IncludeItemTypes": "Movie", 'Fields': 'ProviderIds'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_shows(self):
        path = f"/Items?"
        params = {"Recursive": "true", "IncludeItemTypes": "Series", 'Fields': 'ProviderIds'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_show_by_name(self, showName=None):
        path = f"/Items?"
        params = {"Recursive": "true", "SearchTerm": showName, "IncludeItemTypes": "Series", 'Fields': 'ProviderIds'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_movie_by_provider_id(self, providerId=None):
        path = f"/Items?"
        params = {"Recursive": "true",'AnyProviderIdEquals': providerId, 'Fields': 'ProviderIds,TagItems,Tags', 'IncludeItemTypes': 'Movie'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_series_by_provider_id(self, providerId=None):
        path = f"/Items?"
        params = {"Recursive": "true",'AnyProviderIdEquals': providerId, 'Fields': 'ProviderIds,TagItems,Tags'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_episodes(self, parentID=None):
        path = f"/Items?"
        params = {"Recursive": "true", "ParentId": parentID, "IncludeItemTypes": "Episode", "IsPlayed": "False", 'Fields': 'ProviderIds'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def get_emby_seasons(self, parentID=None):
        path = f"/Items?"
        params = {"Recursive": "true", "ParentId": parentID, "IncludeItemTypes": "Season", 'Fields': 'ProviderIds'}
        cmd = path + urlencode(params)
        return self._call_api(cmd, 'GET')
    def set_emby_poster(self, imageUrl, itemId):
        payload = ()
        data = {"Url":imageUrl}
        path = f"/Items/{itemId}/Images/Primary/0/Url"
        return self._call_api(path, 'POST', payload, json.dumps(data))
    def update_emby_media(self, itemId, data):
        payload = ()
        path = f'/Items/{itemId}'
        return self._call_api(path, 'POST', payload, json.dumps(data))
    def ValidateTagExists(self, input, tag):
        for item in input:
            if item['Name'] == tag:
                return True
        return False
    def GetEmbyIDFromUsername(self, username):
        path = f"/Users"
        params = {}
        cmd = path + urlencode(params)
        users = self._call_api(cmd, 'GET')
        for u in users:
            if u['Name'] == username:
                return u['Id']
        return None



        
print("Getting Library Items. This can take a while.")
embyClient = emby(EMBY_URL.rstrip('/'), EMBY_APIKEY, VERIFY_SSL)

account = MyPlexAccount(PLEX_TOKEN)
plexClient = account.resource(PLEX_SERVER_NAME).connect()

plexMovieLibraries = PLEX_MOVIE_LIBRARIES.split(",")
plexSeriesLibraries = PLEX_SERIES_LIBRARIES.split(",")

unmatchedMovies = []
unmatchedSeries = []

EMBY_USER_ID = embyClient.GetEmbyIDFromUsername(EMBY_USERNAME)


print("\nStarting Movie Matching.")
for library in  plexMovieLibraries:
    for plexMovie in plexClient.library.section(library).search():
        posterUpdated = False
        migrated = ""

        for id in plexMovie.guids:
            provder = id.id.split('://')
            provderId = id.id.replace('://','.')
            em = embyClient.get_emby_movie_by_provider_id(provderId)
            if len(em['Items']) > 0 and posterUpdated == False:
                for m in em['Items']:
                    migrated = embyClient.ValidateTagExists(m['TagItems'],"migrated")
                    if migrated == False:
                        embyClient.set_emby_poster(plexMovie.posterUrl, m["Id"])
                        posterUpdated = True

                        try:
                            data = embyClient.get_emby_item(m['Id'], EMBY_USER_ID)
                            data['Name'] = plexMovie.title
                            if plexMovie.originalTitle != None:
                                data['OriginalTitle'] = plexMovie.originalTitle
                            data['ForcedSortName'] = plexMovie.titleSort
                            data['OfficialRating'] = plexMovie.contentRating
                            for label in plexMovie.labels:
                                tagExists = embyClient.ValidateTagExists(data['TagItems'],label.tag)
                                if tagExists == False:
                                    data['TagItems'].append({'Name': label.tag, 'Id': label.id})
                            data['TagItems'].append({'Name': "migrated", 'Id': "123456"})

                            embyClient.update_emby_media(m['Id'], data)
                        except:
                            print(f'Error updating metadata for - {m["Name"]}')

                        print(f"movie match success using {provder[0]} -- {m['Name']}")
                    else:
                        print(f"Movie already migrated - {m['Name']}")
                if posterUpdated == True or migrated == True:
                    break

        if posterUpdated == False and migrated == False:
            unmatchedMovies.append(plexMovie.title)
data = ''

print("\nStarting TV Series Matching.")
for library in  plexSeriesLibraries:
    for plexShow in plexClient.library.section(library).search():
        plexSeasons = plexShow.seasons()
        posterUpdated = False
        migrated = ""

        for id in plexShow.guids:
            provider = id.id.split('://')
            embyShow = embyClient.get_emby_series_by_provider_id(f'{provider[0]}.{provider[1]}')
            if len(embyShow['Items']) > 0 and posterUpdated == False:
                for s in embyShow['Items']:
                    migrated = embyClient.ValidateTagExists(s['TagItems'],"migrated")
                    if migrated == False:
                        embyClient.set_emby_poster(plexShow.posterUrl, s["Id"])
                        posterUpdated = True
                        print(f"show match success using {provider[0]} -- {s['Name']}")
                        try:
                            data = embyClient.get_emby_item(s['Id'], EMBY_USER_ID)
                            data['Name'] = plexShow.title
                            if plexShow.originalTitle != None:
                                data['OriginalTitle'] = plexShow.originalTitle
                            data['ForcedSortName'] = plexShow.titleSort
                            data['OfficialRating'] = plexShow.contentRating
                            for label in plexShow.labels:
                                tagExists = embyClient.ValidateTagExists(data['TagItems'],label.tag)
                                if tagExists == False:
                                    data['TagItems'].append({'Name': label.tag, 'Id': label.id})
                            data['TagItems'].append({'Name': "migrated", 'Id': "123456"})
                            embyClient.update_emby_media(s['Id'], data)
                        except:
                            print(f'Error updating metadata for - {m["Name"]}')
                    else:
                        print(f'Series already migrated - {s["Name"]}')
                    
                    if migrated == False:
                        embySeasons = embyClient.get_emby_seasons(s["Id"])
                        for ps in plexSeasons:
                            for es in embySeasons['Items']:
                                if f"Season {ps.seasonNumber}" == es['Name']:
                                    embyClient.set_emby_poster(ps.posterUrl, es["Id"])
                                    print(f"Season match - {es['Name']}")

            if posterUpdated == True or migrated == True:
                break

        if posterUpdated == False and migrated == False:
            unmatchedSeries.append(plexShow.title)

if len(unmatchedMovies) > 0:
    print("\nMatch not found for the following Movies:")
    for i in unmatchedMovies:
        print(i)
if len(unmatchedSeries) > 0:
    print("\nMatch not found for the following Series:")
    for i in unmatchedSeries:
        print(i)
