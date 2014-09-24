# coding: utf-8

import sys
sys.path.append('/home/plum/kimo_emo')
import pymongo
from Tokenizer import Tokenizer

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

    Returns
    =======
    no return value, insert back to mongo directly

    """
    mongo_addr = 'doraemon.iis.sinica.edu.tw' if 'mongo_addr' not in kwargs else kwargs['mongo_addr']
    mongo_db = 'espanol' if 'espanol' not in kwargs else kwargs['mongo_db']
    mongo_co = 'bk.posts' if 'bk.posts' not in kwargs else kwargs['mongo_co']

    ## connect to mongo
    db = pymongo.Connection(mongo_addr)[mongo_db]
    co = db[mongo_co]

    ## init a CKIP tokenizer
    tok = Tokenizer()
    
    total = co.count()
    for ith, mdoc in enumerate(co.find()):

        if 'parsed' in mdoc:
            print >> sys.stderr, '> %d/%d doc already parsed. skip' % (ith+1, total)
            continue
        
        parsed_sent_lst = []
        for raw_sent in mdoc['content']:

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
        co.update( {"_id": current_id} , {"$set": {"parsed": parsed_sent_lst} })  
