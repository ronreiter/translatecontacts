from __future__ import print_function
import pickle
import googletrans
import os.path
import shelve

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/contacts']

translator = googletrans.Translator()

cache = shelve.open("name_cache.db")
skipped = shelve.open("skipped.db")

def main():
    """Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('people', 'v1', credentials=creds)

    # Call the People API
    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=2000,
        personFields='names,emailAddresses').execute()
    connections = results.get('connections', [])

    for person in connections:
        names = person.get('names', [])
        if names:
            name = names[0].get('displayName')
            givenName = names[0].get('givenName')
            familyName = names[0].get('familyName')

            if not names or not givenName or not familyName:
                 continue   

            if givenName.isascii() and familyName.isascii():
                continue

            if person['resourceName'] in skipped:
                continue

            print(name[::-1])
            print(givenName[::-1])
            print(familyName[::-1])

            # newDisplayName = translator.translate(name, src="he", dest="en").text
            newGivenName = translator.translate(givenName, src="he", dest="en").text if givenName not in cache else cache[givenName]
            newFamilyName = translator.translate(familyName, src="he", dest="en").text if familyName not in cache else cache[familyName]

            print("First name: " + newGivenName)
            print("Last name: " + newFamilyName)

            while True:
                sababa = input("enter (y) to accept, (n) to change, (d) to delete, (s) to skip: ")
                if sababa in ["y", "n", "d", "s"]:
                    break
            
            if sababa == "s":
                skipped[person['resourceName']] = True
                continue

            if sababa == "d":
                res = service.people().deleteContact(
                    resourceName=person['resourceName'], 
                ).execute()
                print("Contact deleted!")
                continue

            if sababa == "n":
                inputNewGivenName = input("First name (enter to copy): ")
                inputNewFamilyName = input("Last name (enter to copy): ")
                if inputNewGivenName:
                    newGivenName = inputNewGivenName
                if inputNewFamilyName:
                    newFamilyName = inputNewFamilyName
            
            cache[givenName] = newGivenName
            cache[familyName] = newFamilyName

            print('changing to %s %s' % (newGivenName, newFamilyName))
            service.people().updateContact(
                resourceName=person['resourceName'], 
                body={
                    'resourceName': person['resourceName'], 
                    'etag': person['etag'],
                    'names': [
                        {
                            'givenName': newGivenName,
                            'familyName': newFamilyName,
                            # 'displayName': newDisplayName
                        }
                    ]
                },
                updatePersonFields='names'
            ).execute()



if __name__ == '__main__':
    main()

