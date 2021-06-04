import sys
sys.path.insert(1, './PIL')
from PIL import Image
import boto3
from io import BytesIO


def lambda_handler(event, context):
	"""
		converts image type to webp to reduce file size
	"""
	trigger_bucket = event['Records'][0]['s3']['bucket']['name']#triggered bucket set from lambda
	image_name = event['Records'][0]['s3']['object']['key']#file name inserted from s3
	print (trigger_bucket)
	print (image_name)
	s3 = boto3.client('s3')
	load_image = s3.get_object(Bucket=trigger_bucket, Key=image_name)#load new image inserted from buckett
	image_body = load_image['Body'].read()#read image
	
	BUCKET_NAME = 'BUCKET-NAME'

	split_name = image_name.split('.')
	webp_name = split_name[0].replace('news/', '') + '.webp'
	image = Image.open(BytesIO(image_body)).convert("RGB")

	width, height = image.size
	orig_size_webp = BytesIO()
	image.save(orig_size_webp, 'WEBP')
	orig_size_webp.seek(0)
	orig_object_key = 'post/webp/' + webp_name

	#saved converted image to original size
	s3.put_object(Bucket=BUCKET_NAME, Key=orig_object_key, Body=orig_size_webp, ContentType='image/webp', CacheControl='public, max-age=5184000', ACL='public-read')
	print ('orignal image size saved...')

	sizes = [696, 100]
	for size in sizes:
		object_key = 'post/' + str(size) + 'x/' + webp_name
		if size == 696:
			#resize image to 696x
			resize_height_percentage = size / width
			new_height = int(height * resize_height_percentage)
			resized_image = image.resize((size,new_height))
			resized_buffer_image = BytesIO()
			resized_image.save(resized_buffer_image, 'WEBP')
			resized_buffer_image.seek(0)

			#saved converted image to s3 696x bucket
			s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=resized_buffer_image, ContentType='image/webp', CacheControl='public, max-age=5184000', ACL='public-read')
			print ('696 image size saved...')

		else:
			#centered crop converted image to 100x100
			resize_height_percentage = 100 / height
			new_width = int(width * resize_height_percentage)
			resize_image_crop = image.resize((new_width, 100))
			left = (new_width - 100) / 2
			top = 0
			right = left + 100
			bottom = 100
			cropped_image = resize_image_crop.crop((left, top, right, bottom))
			cropped_buffer_image = BytesIO()
			cropped_image.save(cropped_buffer_image, 'WEBP')
			cropped_buffer_image.seek(0)

			#saved converted image to s3 100x bucket
			s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=cropped_buffer_image, ContentType='image/webp', CacheControl='public, max-age=5184000', ACL='public-read')
			print ('100 image size saved...')

	return 'Success'
