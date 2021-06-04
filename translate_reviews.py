# -*- coding: utf-8 -*-
import pymysql.cursors
import json
import boto3
import logging
from pymysql.err import IntegrityError

"""
	Translate non english critic reviews using AWS Translate.
	If review already translated, it will return the translated review. If not
	it will convert the critic review and append and save to s3 bucket and database.
"""


def database_connection():
	"""
		database config
	"""
	open_configs = open('/path/to/config.json').read()
	load_configs = json.loads(open_configs)
	current_server = load_configs['production']
	user = current_server['user']
	password = current_server['password']
	db = current_server['db']
	server_host = current_server['host']
	conn = pymysql.connect(
							user=user,
							passwd=password,
							db=db,
							host=server_host,
							charset="utf8",
							use_unicode=True
						)
	cursor = conn.cursor()

	return [cursor, conn]


def get_conclusion_review(review_id):
	"""
		I already got a script that runs and saves untranslated reviews to s3 Bucket
	"""
	print ('get_conclusion_review() function...')
	s3 = boto3.client("s3")
	get_translated_quote = s3.get_object(Bucket="critic-translation", Key="not_translated_reviews.json")
	load_untranslated_file = json.loads(get_translated_quote['Body'].read())

	str_rev_id = str(review_id)
	if str_rev_id in load_untranslated_file:
		print ('returning untranslated review from s3 bucket...')
		return load_untranslated_file[str_rev_id]

	else:
		db_connect = database_connection()
		cursor = db_connect[0]
		conn = db_connect[1]
		print ('query reviews from critic_reviews table...')
		cursor.execute("SELECT critic_reviews.critic_quote, languages.language_code FROM critic_reviews INNER JOIN languages ON languages.language_id=critic_reviews.language_id WHERE critic_reviews.critic_review_id=%s", [review_id])
		conclusion = cursor.fetchone()

		return conclusion


def add_new_translation(review_id, new_translation):
	"""
		saves translated critic review to database
	"""
	print ('add_new_translation() function...')
	db_connect = database_connection()
	cursor = db_connect[0]
	conn = db_connect[1]

	cursor.close()
	conn.close()
	try:
		print ('inserting new translation...')
		insert_new_trans = ("INSERT INTO critic_review_translations (critic_review_id, translation, language_id, translation_status) VALUES (%s, %s, %s, %s)")
		data_trans = (review_id, new_translation,1, 1)
		cursor.execute(insert_new_trans, data_trans)
		conn.commit()
		print ("new translation added to critic_review_translations table...")
	except IntegrityError as ie:
		print ('integrity error, duplicate entry...')
		print ('continue...')
	

def translateReview(event, context):
	"""
		translate non english reviews
	"""
	print ('translateReview() function...')
	critic_review_id = event['review_id']
	s3 = boto3.client("s3")
	get_translated_quote = s3.get_object(Bucket="critic-translation", Key="translated_reviews.json")
	load_translated_file = json.loads(get_translated_quote['Body'].read())

	try:
		translated_quote = load_translated_file[str(critic_review_id)]
		print ("loaded from dictionary...")
		return translated_quote

	except KeyError:
		print ('review not in dictionary...')

		review_data = get_conclusion_review(critic_review_id)
		conclusion = review_data[0]#original conclusion
		lang_code = review_data[1]#language code of the original critic reviews
		print (conclusion)
		print (lang_code)

		translator = boto3.client(service_name='translate')
		print ('translating...') 
		result = translator.translate_text(Text=conclusion, SourceLanguageCode=lang_code, TargetLanguageCode='en')
		print ('result {0}...'.format(result))

		translated_quote = result.get('TranslatedText')

		add_new_translation(critic_review_id, translated_quote)

		return translated_quote

