from xmlrpc.client import ResponseError
from minio import Minio
import os, glob
import datetime

timestr = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M') 

def getMinioClient(access,secret):
  return Minio(
    'localhost:9000',
    access_key=access,
    secret_key=secret,
    secure=False
  )

if __name__ == '__main__':
  minioClient = getMinioClient('admin', 'password')

  if (not minioClient.bucket_exists('test')):
    try:
      minioClient.make_bucket('test')
    except ResponseError as identifier:
      raise

  if (not minioClient.bucket_exists('test2')):
    try:
      minioClient.make_bucket('test2')
    except ResponseError as identifier:
      raise
  
  try:
    for filename in glob.glob('*.tif'):
      with open(os.path.join(os.getcwd(), filename), 'rb') as testfile:
        statdata = os.stat(filename)
        content_type='application/octet-stream'
        metadata = {
          'x-amz-meta-testing': 'value',
          'datetime': timestr,
        }
        minioClient.put_object(
          'test',
          filename+'-metadata',
          testfile,
          statdata.st_size,
          content_type,
          metadata
        )
  except ResponseError as identifier:
    pass 

  try:
    for filename in glob.glob('*.bin'):
      with open(os.path.join(os.getcwd(), filename), 'rb') as testfile:
        statdata = os.stat(filename)
        minioClient.put_object(
          'test2',
          filename,
          testfile,
          statdata.st_size
        )
  except ResponseError as identifier:
    pass 
