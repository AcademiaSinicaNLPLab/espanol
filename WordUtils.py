# coding: utf-8

import pymongo
from collections import Counter
import pickle
import os
import logging

class WordUtils(object):
    """
    Utilities for word operations such as co-occurrence and Mutural Information
    """
    def __init__(self, **kwargs):

        loglevel = logging.DEBUG if 'verbose' in kwargs and kwargs['verbose'] == True else logging.INFO
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)  

        ## base: could be post-based or sentence-based
        self.based = 'post' if 'based' not in kwargs else kwargs['based']

        self.AllPairs = {}
        self.PMI = {}
        
    def build_dist(self, path, **kwargs):
        """
        build(+save)/load word distribution

        Parameters
        ==========
        path: str
            path to the all-pairs, which contains the mapping of { post-id : pairs }
            where `pairs` are the list of ( word, Pos-tag ) tuples

        options:

            mongo_addr: str
            mongo_db:   str
            mongo_cos:  list
            override:   True/False
        """

        ## mongodb
        mongo_addr = 'doraemon.iis.sinica.edu.tw' if 'mongo_addr' not in kwargs else kwargs['mongo_addr']
        mongo_db = 'espanol' if 'mongo_db' not in kwargs else kwargs['mongo_db']

        ## support multiple target collections
        ## mongo_cos = ['bk.posts', 'qy.posts']
        mongo_cos = ['bk.posts'] if 'mongo_cos' not in kwargs else kwargs['mongo_cos']

        override = False if 'override' not in kwargs else kwargs['override']

        ## check if self.AllPairs exists
        if self.AllPairs and not override:
            logging.info('AllPairs already exists')
            return False

        if os.path.exists(path) and not override:
            logging.info('Load AllPairs from %s' % (path))
            self.AllPairs = pickle.load(open(path))
            return True

        ### fetch data from mongodb
        self.AllPairs = {}
        self.db = pymongo.Connection(mongo_addr)[mongo_db]
        
        for mongo_co in mongo_cos

            self.co = self.db[mongo_co]
            logging.info('Collect posts from %s' % (self.co.full_name))

            total = self.co.count()
            for i, mdoc in enumerate(self.co.find()):
                if 'parsed' not in mdoc or len(mdoc['parsed']) == 0:
                    logging.debug('> skip %d/%d mongo doc' % (i+1, total))
                    continue
                
                logging.debug('> process %d/%d mongo doc' % (i+1, total))
                ## "_id" : ObjectId("5406a2aa3480ad1b9b828c52"),
                ## post_id will be "5406a2aa3480ad1b9b828c52"
                post_id = str(mdoc['_id'])

                pairs = Counter()
                for parsed_sent in mdoc['parsed']:
                    ## parsed_sent
                    # '\u7684(DE)\u3000\u591c\u666f(Na)\u3000\u4e0d\u932f(VH)'

                    spliited = parsed_sent.strip().split(u'　')
                    ## spliited:
                    # [u'\u7684(DE)',
                    #  u'\u591c\u666f(Na)'
                    #  u'\u4e0d\u932f(VH)'] 

                    for word_pos in spliited:
                        token = '('.join(word_pos.split('(')[:-1])
                        postag = word_pos.split('(')[-1].split(')')[0]
                        ## token: \u591c\u666f --> 夜景
                        ## token: Na
                        pairs[ (token,postag) ] += 1

                self.AllPairs[post_id] = pairs

            logging.info('dumping AllPairs into %s' % (path))
            pickle.dump(self.AllPairs, open(path, 'wb'), protocol=2)
            return True

    def build_cooccurrence(self, tag='N', targetList='resources/wordlist.owl.pkl', order=False, case=False):
        """
        calculate post-based, order-nonsenitive co-occurrence

        Parameters
        ==========
        AllPairs: Counter
            { post-id : occurrence distribution }

        tag: str
            filter out the word with the specified part-of-speech tag
        
        targetList: str
            path to the list that contains anchor words
            in this project, the targetList is the list of words appearing in the OWL ontology

        order: True/False
            consider ordering or not
            e.g., if this is set `True`, ("travel", "spain") and ("spain", "travel") are the different word pairs
        """

        ## load target word list
        logging.debug('load targetList from %s' % (targetList))
        wlist = set(pickle.load(open(targetList)))

        ## occurrence of words (post-based)
        self.Occur = Counter()
        ## co-occurrence of words (post-based)
        self.Cooccur = Counter()

        logging.info('calculate occurrence and co-occurrence')
        ## post-based
        for pid in self.AllPairs:

            dist = self.AllPairs[pid]

            ## filter out words
            words = set([w for w,p in dist.keys() if p.startswith(tag)])

            ## intersection with ontology words
            inter = [w for w in words if w in wlist]

            ## pairwise <inter-words>
            pairs = [ (m,n) for m in inter for n in words if m != n]

            ## update co-occurrence
            for pair in pairs:

                pair = map(lambda x:x.lower(), pair) if not case else pair

                key = tuple(sorted(pair)) if not order else pair
                
                self.Cooccur[ key ] += 1

            ## update occurrence
            for word in words:
                word = word.lower() if not case else word
                self.Occur[ word ] += 1

    def build_PMI(self, path):
        """
        pmi(x,y) = log( p(x,y)/p(x)p(y) ) 
            where p(x), p(y) are the probability of the word x and y respectively
            and p(x,y) is the probability of the pair (x,y)
        """
        if os.path.exists(path):
            logging.info('loading PMI from %s' % (path))
            self.PMI = pickle.load(open(path))
            return True

        from math import log
        num_of_post = float(len(self.AllPairs))

        logging.info('calculate PMI of each pair')
        self.PMI = {}
        for pair, count in self.Cooccur.iteritems():
            
            x, y = pair

            f_x, f_y = self.Occur[x], self.Occur[y]
            p_x, p_y = f_x/num_of_post, f_y/num_of_post

            f_x_y = count
            p_x_y = count/num_of_post

            pmi_x_y = log( p_x_y/(p_x*p_y) )

            self.PMI[(x,y)] = pmi_x_y

        logging.info('dumping PMI into %s' % (path))
        pickle.dump(self.PMI, open(path, 'wb'), protocol=2)

    def get_PMI(self, w1, w2, case=False, order=False):
        if not self.PMI:
            logging.error("cannot find PMI data, run `build_PMI(path='...')` first")
            return False
        else:
            pair = [w1, w2] if not case else [w1.lower(), w2.lower()]
            pair = tuple(sorted(pair)) if not order else tuple(pair)
            pair = tuple(pair)

            if pair in self.PMI:
                return self.PMI[pair]
            else:
                logging.warn("can't find the pair", pair, "in PMI data")
                return 0.0

def usage():

    module = __file__.replace('.py','')
    print """
    Usage Examples of %s
    ==================%s

    >> from WordUtils import WordUtils

    >> wu = WordUtils(verbose=True)

    ## To build PMI of certain data:

        >> wu.build_dist(path="resources/all-pairs.pkl")

        or specify the mongo address, collections and override it
        and finally save AllPairs in `resources/new.data.pairs.pkl`
        >> wu.build_dist(path="resources/new.data.pairs.pkl", mongo_addr="your.own.mongo", mongo_cos=["bk.posts", "qy.posts"], override=True)

        >> wu.build_cooccurrence()
        >> wu.build_PMI(path="resources/bk-owl.pmi.pkl")

        or specify a new path for storing PMI data 
        >> wu.build_PMI(path="resources/bk-qy-owl.pmi.pkl")

    ## To find the PMI of certain word pair

        >> wu.get_PMI(w1, w2)
    """ % (module, '='*len(module))

if __name__ == '__main__':
    
    usage()


    
    
    
    


