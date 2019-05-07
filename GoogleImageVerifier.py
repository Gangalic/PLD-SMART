import io
import os

# Imports the Google Cloud client library
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
        

"""
verifier = GoogleImageVerifier('creds.json')
# The name of the image file to annotate
file_name = os.path.join(
    os.path.dirname(__file__),
    '86843854_o.jpg')

# Loads the image into memory and verify it against a label
with io.open(file_name, 'rb') as image_file:
    content = image_file.read()
    validImage = verifier.verify(content,"Stone carving")
    print(validImage)
"""
