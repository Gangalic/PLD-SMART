import io
from io import BytesIO
import os
import sys
from PIL import Image
import pickle
import torch
from torchvision import transforms
import torchvision
from CloudStorage import ImageUploader 

data_transforms = {
    'test': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}

googleCredentialsPath = 'creds.json'
bucket_name='smart_images_dataset'

class CustomImageVerifier:
    def __init__(self,modelPath):
        #torch 
        self.model = torch.load(modelPath,map_location='cpu')
        self.model.eval()
        # cloud storage
        self.imageUploader = ImageUploader(googleCredentialsPath,bucket_name)
        with open('classNames', 'rb') as f:
            self.classNames = pickle.load(f)

    def verify(self,image,targetLabel):
        """"
        tempo_file = open('tmp_image.png','wb')
        tempo_file.write(image)
        tempo_file.close()

        image = Image.open('tmp_image.png')
        """
        
        image = Image.open(BytesIO(image))
        image = data_transforms['test'](image).unsqueeze(0)
        outputs = self.model(image)

        softmax = torch.nn.Softmax()
        probabilities = softmax(outputs)

        _, pred = torch.max(outputs, 1)
        predLabel = self.classNames[pred]
        probaLabel = probabilities[0, pred]

        print('outputs : ', outputs)
        print('pred : ', pred)
        print('outputs[pred] : ', outputs[0, pred])
        print('predLabel : ', predLabel)
        print('probabilities : ', probabilities)
        print('probabilities[pred]', probabilities[0, pred])
        print('probaLabel : ', probaLabel)
        valid  = predLabel == targetLabel and probaLabel > 0.9
        if(valid):
          self.imageUploader.uploadUserImage(image,targetLabel)
        return (valid)

"""
## Use example
verifier = CustomImageVerifier('resnet.pth')

print(verifier.classNames)

# The name of the image file to annotate
file_name = os.path.join(
    os.path.dirname(__file__),
    'bwfruits.jpg')

# Loads the image into memory and verify it against a label
with Image.open(file_name) as image:
    print('Result : ', verifier.verify(image,"pont_raymond_barre"))

"""
