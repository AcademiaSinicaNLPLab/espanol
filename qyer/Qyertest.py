# In 1st level page to extract urls, content tags, titles and userIds from Qyer
from BeautifulSoup import BeautifulSoup
import urllib2

url = urllib2.urlopen("file:///home/wei/projects/espanol/Qyer/0.html").read()

soup = BeautifulSoup (url)
l = soup.findAll(attrs={'class':'bbsForumsTit'})
l[0]
l[0]['class']
l[0].attrs
l[0].findAll('a')
tmp = l[0].findAll('a')[0]
type(tmp)
tmp['href']

qylinks = map(lambda x: x.findAll('a')[0]['href'], soup.findAll(attrs={'class':'bbsForumsTit'}))
infocontent = map(lambda x: x.findAll('em'), soup.findAll(attrs={'class':'bbsForumsInfo'}))
content = map(lambda x: x.text, soup.findAll(attrs={'class':'bbsForumsTit'}))
for c in content:
    print c + '\n'

#save the output result to further use
import pickle
pickle.dump(infocontent, open('infocontent.pkl','w'))
pickle.dump(content, open('content.pkl','w'))
pickle.dump(qylinks,open('qylinks','w'))

#load saved pkl 
import pickle
qylinks = pickle.load(open('qylinks.pkl','r'))
#correct the urls (no need re, with built in function we can do a lot of things)
## method 1
newqylinks = []
for x in qylinks:
	newqylinks.append( 'bbs.qyer.com/'+x )
## method 2
## map
map(lambda x: 'bbs.qyer.com/'+x, qylinks)
## method 3
## list-comprehension
['bbs.qyer.com/'+x for x in qylinks]


# Retrieve all urls of 1st level and download its pages
# http://bbs.qyer.com/forum-18-1.html until /forum-18-350.html
qy1sturl = map(lambda x: 'bbs.qyer.com/forum-18-'+x+'.html',[str(i)for i in range(1,351)])
pickle.dump(qy1sturl, open('qy1sturl.pkl', 'w'))
# Pack all previous HTMLs
import requests
import codecs
# creat a fake ID (copy from one webpage)
agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0'
#In [76]: requests.get(qy1sturl[0])
#Out[76]: <Response [200]>
req = requests.get(qy1sturl[0])# test
req.text
# ajout hidding ID + encoding (see request)
req = requests.get(qy1sturl[0], headers={'User-Agent':agent})# test
req.text

def fetch(url, output):
    with codecs.open(output, 'w', 'utf-8') as f:
        req = requests.get(url, headers={'User-Agent':agent}, encoding='utf-8')
        f.write(req.text)

## method 1
import time
for i, url in enumerate(qy1sturl):
    fetch(url, str(i) + '.html')
    time.sleep(1000)

## method 2
import random

for i, url in enumerate(qy1sturl):
    fetch(url, str(i) + '.html')
    time.sleep(random.random())
#ChunkedEncodingError: IncompleteRead(10 bytes read)
for i in xrange(220, len(qy1sturl)):
    fetch(qy1sturl[i], str(i) + '.html')
    time.sleep(random.random())

# put together qyer's 1st level urls: file:///home/wei/projects/espanol/Qyer 
#!/usr/bin/python
import codecs
import os, sys
import pickle
from BeautifulSoup import BeautifulSoup

path = "/home/wei/projects/espanol/Qyer"
qyhtml = os.listdir(path)

total_links = []

for qypage in qyhtml:
	fn = os.path.join(path,qypage)
	qytext = codecs.open(fn, 'r', 'utf-8').read()
	soup = BeautifulSoup(qytext)
	qytitle = soup.findAll(attrs={'class':'tit'})

	prefix = 'http://bbs.qyer.com/'

	links = []
	for entry in qytitle:
		if entry.has_key('href'):
			links.append( prefix + entry['href'] )

	# links = map(lambda x: prefix+qytitle[x]['href'], [int(i) for i in range(2,26)])

	total_links = total_links + links

	print 'current page', qypage

pickle.dump( total_links, open( 'total_links.pkl' ,'w') )
		

qylinkresult = open("qylinkresult.txt", 'w')
qylinkresult.close()

infocontent = pickle.load(open('infocontent.pkl','r'))
content = pickle.load(open('content.pkl','r'))

# =======================================================================
'''arrange all url from that we retrieve the needed information'''
import pickle
import urllib2
from BeautifulSoup import BeautifulSoup
import time
import random
import os

total_links = pickle.load(open('total_links.pkl'))
links= [u'http://bbs.qyer.com/thread-872174-1.html',u'http://bbs.qyer.com/thread-309793-1.html',u'http://bbs.qyer.com/thread-310976-1.html',u'http://bbs.qyer.com/thread-315596-1.html',u'http://bbs.qyer.com/thread-298502-1.html',u'http://bbs.qyer.com/thread-310877-1.html',u'http://bbs.qyer.com/thread-312747-1.html',u'http://bbs.qyer.com/thread-315503-1.html',u'http://bbs.qyer.com/thread-315495-1.html',u'http://bbs.qyer.com/thread-880582-1.html',u'http://bbs.qyer.com/thread-747220-1.html',u'http://bbs.qyer.com/thread-856045-1.html',u'http://bbs.qyer.com/thread-883918-1.html',u'http://bbs.qyer.com/thread-883255-1.html',u'http://bbs.qyer.com/thread-608840-1.html']

def find_extended_url(total_links):
	ct_links = []

root_folder = 'data'
if not os.path.exists(root_folder): os.mkdir(root_folder)

for lik in total_links:
	
	fn = os.path.join(root_folder, lik.split('/')[-1])
	if os.path.exists(fn):
		print 'read html from %s' % (fn)
		html = open(fn).read()
	else:
		print 'fetch %s and save to %s' % (lik, fn)
		html = urllib2.urlopen(lik).read()
		with open(fn, 'w') as fw:
			fw.write(html)

	soup = BeautifulSoup(html)
	pg_url = soup.findAll(attrs={'class':'pages'})## bs4 resultset
	if len(pg_url)== 0:
		print lik, '=>has no ext. pages'
		continue
	else:
		lks= []
		for ts in pg_url:
			a = ts.findAll('a')
			for t in a:	
				lk = t['href']
				lks.append(lk)
		print lks###eliminate later

				ct_lk= map(lambda x: 'http://bbs.qyer.com/'+x, lks)
				
				ct_lks = []
				for i in ct_lk:
					if i not in ct_lks:
						ct_lks.append(i)
	ct_links = ct_lks+total_links
	print ct_links
	return ct_links

	 
		
		

		

