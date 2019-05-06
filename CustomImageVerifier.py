import io
import os
from PIL import Image
import pickle

#import pytorch
import torch
from torchvision import transforms

import torchvision
print(torchvision.__version__)
print(torch.__version__)

data_transforms = {
    'test': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}


class CustomImageVerifier:
    def __init__(self,modelPath):
        # Instantiates a client
        self.model = torch.load(modelPath,map_location='cpu')
        self.model.eval()

        with open('classNames', 'rb') as f:
            self.classNames = pickle.load(f)

    def verify(self,image,targetLabel):
        image = data_transforms['test'](image).unsqueeze(0)
        # print(image.shape)
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

        return (predLabel == targetLabel and probaLabel > 0.9)


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
