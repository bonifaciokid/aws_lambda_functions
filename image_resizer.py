import sys
sys.path.insert(1, './PIL')
from PIL import Image
import boto3
from io import BytesIO


def lambda_handler(event, context):
	"""
		Coverts image to webp to different sizes.
	"""

	#lambda triggered by new image inserted from S3 bucket
	trigger_bucket = event['Records'][0]['s3']['bucket']['name']
	image_name = event['Records'][0]['s3']['object']['key']

	s3 = boto3.client('s3')
	load_image = s3.get_object(Bucket=trigger_bucket, Key=image_name)
	image_body = load_image['Body'].read()
	
	image = Image.open(BytesIO(image_body)).convert("RGBA")
	width, height = image.size

	split_name = image_name.split('.')
	webp_name = split_name[0] + '.webp'
	try:
		BUCKET_NAME = 'bucket_name'
		sizes = [150, 100, 80]
		for size in sizes:
			print (size)
			if width == height:
				resized_image = image.resize((size,size))
				squared_image = resized_image
			else:
				resize_height_percentage = size / width
				new_height = int(height * resize_height_percentage)
				resized_image = image.resize((size,new_height))

				box = (0, 0, size, size)
				squared_image = resized_image.crop(box)

			resize_buffer_image = BytesIO()
			resized_image.save(resize_buffer_image, 'WEBP')

			squared_buffer_image = BytesIO()
			squared_image.save(squared_buffer_image, 'WEBP')

			resize_buffer_image.seek(0)
			squared_buffer_image.seek(0)

			s3_resource = boto3.resource('s3')
			reg_object_key = 'reg/' + str(size) + 'x/' + webp_name
			sqr_object_key = 'sqr/' + str(size) + 'x/' + webp_name

			#regular image converted
			s3.put_object(Bucket=BUCKET_NAME, Key=reg_object_key, Body=resize_buffer_image, ContentType='image/webp', CacheControl='public, max-age=31536000', ACL='public-read')
			print ('regular image saved...')

			#sqaured image converted
			s3.put_object(Bucket=BUCKET_NAME, Key=sqr_object_key, Body=squared_buffer_image, ContentType='image/webp', CacheControl='public, max-age=31536000', ACL='public-read')
			print ('squared image saved...')
			print (webp_name)

		return 'success'
		
	except OSError as ose:
		return ose
