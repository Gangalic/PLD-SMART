from google.cloud import storage
from PIL import Image
import io
import base64
import uuid

class ImageUploader:
  def __init__(self,googleCredentialsPath,bucket_name):
    storage_client = storage.Client.from_service_account_json(googleCredentialsPath)
    self.bucket = storage_client.get_bucket(bucket_name)

  def uploadUserImage(self,image,directory):  
      blob = self.bucket.blob(directory + '/' + str(uuid.uuid4()))
      blob.upload_from_string(image)

##Use Example
googleCredentialsPath = 'creds.json'
bucket_name='smart_images_dataset'
#create uploader
uploader = ImageUploader(googleCredentialsPath,bucket_name)
# read and encode image
im = Image.open('cat.jpg')
buffered = io.BytesIO()
im.save(buffered, format="JPEG")
encoded = base64.b64encode(buffered.getvalue())
#decode base64 image
image = base64.b64decode(encoded)
uploader.uploadUserImage(image,'statue')




