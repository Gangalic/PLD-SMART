import io
import os
import requests
import json
from google.cloud import vision
from google.cloud.vision import types


class GoogleImageVerifier:
    def __init__(self,googleCredentialsPath):
        # Instantiates a client
        self.client = vision.ImageAnnotatorClient.from_service_account_json(
            googleCredentialsPath)  

    def verify(self,image,targetLabel):
        #create image type
        image = types.Image(content=image)
        # Performs label detection on the image file
        response = self.client.label_detection(image=image)
        labels = response.label_annotations
        for label in labels:
            print(f'{label.description} : {label.score}')
        for label in labels:
            if (label.description == targetLabel and label.score > 0.55):
                return True 
        return False

    def getLabels(self,searchTerm):
        imageUrl = getImagesUrl(searchTerm,1)[0]
        response = self.client.label_detection({
         'source': {'image_uri': imageUrl}
        }, max_results= 5)
        annotations = response.label_annotations
        labels=[]
        for annotation in annotations:
          labels.append(annotation.description)
        return labels

def getImagesUrl(searchTerm, numResults):
    params={
        'q': searchTerm,
        'cx': '011687418734408437358:mbfpvhsp4bm',
        'searchType': 'image',
        'num': numResults,
        'key': os.environ['CUSTOM_SEARCH_API_KEY']
    }
    headers = {
        'Accept': 'application/json'
    }
    url = 'https://www.googleapis.com/customsearch/v1'
    r = requests.get(url, params=params, headers=headers)
    json_data = json.loads(r.text)['items']
    links = []
    for item in json_data:
        links.append(item['link'])
    return links

# ## Use example
# verifier = GoogleImageVerifier('creds.json')
# verifier.getLabels('arbre')#get available labels for a term
# verifier.verify(content,"Stone carving") #verify an image against a target label


