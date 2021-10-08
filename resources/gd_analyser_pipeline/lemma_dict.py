#40% slower than dict for search, but needs 2 seconds to be loaded

# find_tagged_string_in_dict return None is the string is absent, [] if POS is not found

def add_to_dict(d, string, lemma):
    if d == None:
        if string == '':
            return { 'lemmas': [lemma]}
        else:
            return { string[0]: (add_to_dict(None, string[1:], lemma)) }
    else:
        if string == '':
            lemmas = d.get('lemmas')
            if lemmas != None:
                new_lemmas = [lemma for lemma in lemmas]
                new_lemmas.append(lemma)
                d['lemmas'] = new_lemmas
            else:
                d['lemmas'] = [lemma]
            return d 
        else:
            value = d.get(string[0])
            d[string[0]] = (add_to_dict(value, string[1:], lemma))
            return d


def find_tagged_string_in_dict(d, string, tag):
    if d == None:
        return None
    if string == '':
        lemmas = d.get('lemmas')
        if lemmas == None:
            return None
        return [tagged_lemma[0] for tagged_lemma in lemmas if tagged_lemma[1] == tag]
    value = d.get(string[0])
    return find_tagged_string_in_dict(value, string[1:], tag)


def find_string_in_dict(d, string):
    if d == None:
        return None
    if string == '':
        return d.get('lemmas')
    value = d.get(string[0])
    return find_string_in_dict(value, string[1:])


