# coding: utf-8

from WordUtils import WordUtils

if __name__ == "__main__":

	wu = WordUtils(verbose=True)

	wu.build_dist(path="resources/all-pairs.pkl")

	wu.build_cooccurrence()

	wu.build_PMI(path="resources/bk-owl.pmi.pkl")

	print wu.get_PMI(u'交通', u'西班牙')
