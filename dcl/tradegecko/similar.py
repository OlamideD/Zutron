
#dcl.tradegecko.similar.jelly
def jelly():
    import jellyfish
    a = u'Korle Bu Teaching Hospital Sickle Cell Dept'
    b = u'Korle Bu Teaching Hospital'
    # a = u'x'
    # b = u'a'
    print jellyfish.levenshtein_distance(a,b)
    print jellyfish.jaro_distance(a,b)
    print jellyfish.damerau_levenshtein_distance(a,b)
    # print jellyfish.match_rating_comparison(a,b)

    from fuzzywuzzy import fuzz

    print fuzz.ratio(a,b)