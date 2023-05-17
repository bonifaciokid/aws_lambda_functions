"""
- converts image to WEBP format and saves to S3 Bucket
"""
import sys
import boto3
from io import BytesIO
from PIL import Image
sys.path.insert(1, './PIL')


S3_CLIENT = boto3.client('s3')


def put_obect_to_s3_bucket(bucket_name, object_key, image_body):
    """
    - Upload image to S3 bucket
    - Args
        - bucket_name
            - string
            - s3 bucket
        - object_key
            - string
            - object key
            - this is where you add if sub bucket is required 'sub-bucket/image.webp'
        - image_body
            - image buffer
    - Return None
    """
    S3_CLIENT.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=image_body,
        ContentType='image/webp',
        CacheControl='public, max-age=31536000',
        ACL='public-read'
    )
    print('regular image saved...')


def lambda_handler(event, context):
    """
    - Coverts image to webp to different specific sizes.
    - Sizes will be the sub bucket
    """

    #lambda triggered by new image inserted from S3 bucket
    trigger_bucket = event['Records'][0]['s3']['bucket']['name']
    image_name = event['Records'][0]['s3']['object']['key']

    #load image
    load_image = S3_CLIENT.get_object(Bucket=trigger_bucket, Key=image_name)
    image_body = load_image['Body'].read()

    #open image
    image = Image.open(BytesIO(image_body)).convert("RGBA")
    width, height = image.size

    #build file name
    split_name = image_name.split('.')
    webp_name = split_name[0] + '.webp'
    try:
        bucket_name = 'bucket_name'
        sizes = [500, 400, 300, 250, 200, 150, 100, 80]
        for size in sizes:
            print(size)
            #resize image
            if width == height:
                resized_image = image.resize((size, size))
                squared_image = resized_image
            else:
                resize_height_percentage = size / width
                new_height = int(height * resize_height_percentage)
                resized_image = image.resize((size, new_height))

                box = (0, 0, size, size)
                squared_image = resized_image.crop(box)

            #save image buffer
            resize_buffer_image = BytesIO()
            resized_image.save(resize_buffer_image, 'WEBP')
            resize_buffer_image.seek(0)
            reg_object_key = f"reg/{size}x/{webp_name}"

            #upload regular image
            put_obect_to_s3_bucket(bucket_name, reg_object_key, resize_buffer_image)
            print('regular image saved...')

            #save image buffer
            squared_buffer_image = BytesIO()
            squared_image.save(squared_buffer_image, 'WEBP')
            squared_buffer_image.seek(0)
            sqr_object_key = f"sqr/{size}x/{webp_name}"

            #upload squared image converted
            put_obect_to_s3_bucket(bucket_name, sqr_object_key, squared_buffer_image)
            print('squared image saved...')

        return {'message': 'success'}

    except OSError as ose:
        return ose
