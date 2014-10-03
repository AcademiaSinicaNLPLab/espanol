# coding: utf-8

import sys
sys.path.append('/home/plum/kimo_emo')
import pymongo
from Tokenizer import Tokenizer

def toTraditionalChinese(dbName, collectionName):
    import jianfan

    """
    Parameters
    ==========
    dbName
    collectionName
    """
    db = pymongo.Connection('doraemon.iis.sinica.edu.tw')[dbName]
    co = db[collectionName]
    
    total = co.count()
    for i, mdoc in enumerate(co.find()):
        if "content" not in mdoc or not mdoc["content"]: continue
        try: 
            cht_content = jianfan.jtof( mdoc["content"] )
            print '(%d/%d) convert successfully' % (i+1, total)
        except: 
            print '(%d/%d) fail to convert' % (i+1, total)
            cht_content = mdoc["content"]

        co.update({'_id':mdoc['_id']}, { '$set': { 'cht_contents': cht_content } })

def tokenize_all(**kwargs):
    """
    tokenize all sentences in mongodb

    Example
    =======
    tokenize_all(mongo_addr="localhost", mongo_db="espanol", mongo_co="bk.posts")

    Parameters
    ==========
    mongo_addr: str
        address to mongodb
    mongo_db: str
        db_name in mongodb
    mongo_co: str
        collection_name in mongodb    

    source_field: str
        the source field name in mongo, e.g., 'content'
    target_field: str
        the target field name in mongo, e.g., 'parsed'

    Example
    =======
    >> from preprocessing import tokenize_all
    >> tokenize_all(mongo_co='qy.posts', source_field='cht_contents', target_field="parsed")

    Returns
    =======
    no return value, insert back to mongo directly

    """
    mongo_addr = 'doraemon.iis.sinica.edu.tw' if 'mongo_addr' not in kwargs else kwargs['mongo_addr']
    mongo_db = 'espanol' if 'mongo_db' not in kwargs else kwargs['mongo_db']
    mongo_co = 'bk.posts' if 'mongo_co' not in kwargs else kwargs['mongo_co']

    source_field = 'content' if 'source_field' not in kwargs else kwargs['source_field']
    target_field = 'parsed' if 'target_field' not in kwargs else kwargs['target_field']

    ## connect to mongo
    db = pymongo.Connection(mongo_addr)[mongo_db]
    co = db[mongo_co]

    ## init a CKIP tokenizer
    tok = Tokenizer()
    
    total = co.count()
    for ith, mdoc in enumerate(co.find()):

        if target_field in mdoc:
            print >> sys.stderr, '> %d/%d doc already parsed. skip' % (ith+1, total)
            continue
        
        if source_field not in mdoc:
            print >> sys.stderr, '> %d/%d has no field named %s' % (ith+1, total, source_field)
            continue

        parsed_sent_lst = []
        for raw_sent in mdoc[source_field]:

            ## sent: 你好... (u'\u4f60\u597d...')
            ## ckip accept '\xe4\xbd\xa0\xe5\xa5\xbd' as input
            try:
                parsed_sent = tok.tokenizeStr( raw_sent.encode('utf-8') ).decode('utf-8')
            except:
                ## tokenize error
                ## keep the raw sentence
                parsed_sent = raw_sent
                print >> sys.stderr, '! tokenize error'

            parsed_sent_lst.append( parsed_sent )
        
        ## update
        print >> sys.stderr, '> %d/%d doc parsed. update' % (ith+1, total)
        current_id = mdoc["_id"]
        co.update( {"_id": current_id} , {"$set": { target_field : parsed_sent_lst} })  
