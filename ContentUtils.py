# coding: utf-8

import pymongo

'''UtilsContent for content operations such as content extraction for individual pairs 
or contentextraction for group (top 10 pairs). 
eg.,
search_pairs = [(u'分類', u'西班牙'),(u'教會', u'西班牙'),(u'西班牙', u'餅'),(u'刑法', u'西班牙'),(u'西班牙', u'革命'),(u'西班牙', u'體育場'),(u'印度',u'西班牙'),(u'傳真',u'西班牙'),(u'休閒', u'西班牙'),(u'國會',u'西班牙')]
'''
db = pymongo.Connection('localhost')['espanol'] 
mongo_cos = ['bk.posts', 'qy.posts']
for mongo_co in mongo_cos:
	co =db[mongo_co]
	
	objective_post_id = {}
	for mdoc in co.find():
		if 'parsed' not in mdoc or len(mdoc['parsed']) == 0:
			continue	
			post_id = str(mdoc['_id'])
			for parsed_content in mdoc['parsed']:
				if u'分類'in parsed_content:
					print 'found tk1'
				else: 
					continue	
					if u'西班牙' in parsed_content:
						print 'in', post_id, 'found both terms'
					else:
						continue
					
			objective_post_id [post_id]= parsed_content
