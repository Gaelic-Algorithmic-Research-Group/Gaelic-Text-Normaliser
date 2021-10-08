from .lexicon import Lexicon
from fuzzywuzzy import fuzz
from fuzzywuzzy.fuzz import ratio
from nltk import ngrams, bigrams
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from resources.gd_analyser_pipeline.gd_analyser import job_load, simple_tag, tag
from tqdm import tqdm
import sys, re, argparse, string

bad_comma = re.compile("',\"")  # words where the comma is joined on to the last apostrophe
ps = PorterStemmer()


punctuation = string.punctuation
punctuation += "“``''’”"
lonely_prefix=re.compile(r" [tnh] \w")

common_fixes = re.compile(f"deagh-"
                          "|dheagh-"
                          "|seann-"
                          "|sheann-"
                          "|t-seann-"
                          "|fìor-"
                          "|fhìor-"
                          "|dh'fhìor-"
                          "|droch-"
                          "|dhroch-"
                          "|prìomh-"
                          "|phrìomh-"
                          )

cmap = re.compile("sp"
"|sc"
"|st"
"|chd"
"|nn"
"|rr"
"|ll"
"|cn"
"|gn"
"|chn"
"|ghn"
"|mh"
"|dh"
"|str"
"|shtr"
"|sb"
"|sg"
"|sd"
"|c"
"|n"
"|r"
"|l"
"|cr"
"|gr"
"|chr"
"|ghr"
"|bh"
"|gh"
"|sr"
"|shr"
"|ich"
"|ith"
"|mp"
"|mb"
"|nd"
"|nt"
"|io"
)



cons_map = {
    
    'io' : 'ea',
    'ich' : 'ith',
    'mp' : 'mb',
    'nd' : 'nt',
    'sc' : 'sg',
    'ith' : 'ich',
    'mb' : 'mp',
    'nt' : 'nd',
    'sd' : 'st',
    'chd' : 'c',
    'nn' : 'n',
    'rr' : 'r',
    'll' : 'l',
    'cn' : 'cr',
    'gn' : 'gr',
    'chn' : 'chr',
    'ghn' : 'ghr',
    'mh' : 'bh',
    'dh' : 'gh',
    'str' : 'sr',
    'shtr' : 'shr',
    'sb': 'sp',
    'c': 'chd',
    'n': 'nn',
    'r': 'rr',
    'l': 'll',
    'cr': 'cn',
    'gr': 'gn',
    'chr': 'chn',
    'ghr': 'ghn',
    'bh': 'mh',
    'gh': 'dh',
    'sr': 'str',
    }


# teile = re.compile("|t'èile"
#                    "|t'éile"
#                    "|t'eile")

spaces = re.compile('  ')

def space_reduce(line):
    line = re.sub('\t', ' ', line)
    space_matches = re.findall(spaces, line)
    for match in space_matches:
        line = re.sub(spaces, ' ', line)
        
    return line 

def fix_lonely_prefix(line):

    search = re.findall(lonely_prefix, line)
    
    if search:

        for token in search:
            token = token[1:]
            subbed = re.sub(' ','-', token)
            line = re.sub(token, subbed, line)

    return line

def pre_fix_regex(token):
    match = re.match(common_fixes, token)
    if match:
        token = re.sub(match.group(0), '{} '.format(match.group(0)[:-1]), token)

        return token


def add_hyphen(bigram, normaliser=None):
    hyphenated = '-'.join(bigram.split(' '))

    lookup = normaliser.lexicon.lexicon_lookup(hyphenated)

    if lookup and lookup != 'gaelic_words':

        return {'lexicon': lookup,
                'resolved': normaliser.lexicon.resolve_token(hyphenated, lookup),
                'rule': add_hyphen.__name__}

    else:
        return None


def add_last_vowel(token, normaliser):
    for i in ['a', 'e', 'i', 'o', 'u']:

        added_a = f'{token}{i}'

        lookup = normaliser.lexicon.lexicon_lookup(added_a)

        if lookup == 'gaelic_words':
            return {'lexicon': lookup,
                    'resolved': added_a,
                    'rule': add_last_vowel.__name__}

        elif lookup and lookup != 'gaelic_words':

            return {'lexicon': lookup,
                    'resolved': normaliser.lexicon.resolve_token(added_a, lookup),
                    'rule': add_last_vowel.__name__}

        else:
            return None

def consonant_swap(raw_token, normaliser):
    
    matches = re.findall(cmap, raw_token)
    
    token = raw_token
    
    for match in matches:

        if match in cons_map:
            
            token = re.sub(match, cons_map[match], token)
            lookup = normaliser.lexicon.lexicon_lookup(token)
            
            if lookup == 'gaelic_words':
                return {'lexicon': lookup,
                        'resolved': token,
                        'rule': consonant_swap.__name__}
                
        token=raw_token

    return None

def apostroph_for_ngram_norm(line):
    line = re.sub(all_apostrophes, "'", line)
    return line


def check_capitalised(token):
    """
    Script to check if token is capitalised
    this is used in the rules
    """

    caps = re.compile('^[A-Z]')

    if re.match(caps, token):
        return True
    return None


upper = re.compile(r'[A-Z]')


def check_capitalized(dec_map, og_map, resolved=None):
    """
    This is for the decoding
    """

    if re.match(upper, og_map):
        dec_map['resolved'] = dec_map['resolved'].capitalize()

    return dec_map


def clean_token(token):
    """
    Removes symbols from a token
    """

    clean = re.compile(r'[§%]')
    return re.sub(clean, '', token)


def clean_token_extensive(token):
    patterns = re.compile("[\.£$*\",”\(\)\[\]!:“&;?˩˧]+"  # Punctuation
                          "|<eng>|<gai>"  # language tags
                          "|[$£]\d+\.\d+"  # Currency
                          "| '\w' "  # Words in quotes

                          )
    fix_hyphenated = re.compile(r'[a-z]+- [a-z]+')
    for i in re.findall(fix_hyphenated, token):
        fixed = re.sub(' ', '', i)
        token = re.sub(i, fixed, token)

    token = re.sub(patterns, '', token)
    token = re.sub(r'\n', ' ', token)  # white space markers
    token = re.sub(r'\s+', ' ', token)  # double spacing
    return token


def decode_maps(tok_map, punct_map, og_map, last_method=None):
    punct_map.update(tok_map)
    #print(punct_map)
    # print(sorted(punct_map.items()))
    line = []
    for i in sorted(punct_map):

        if type(punct_map[i]) == dict:

            if 'resolved' in punct_map[i]:
                # resolved_tok = check_capitalized(punct_map[i]['raw_token'], punct_map[i]['resolved'])
                # print(resolved_tok)

                punct_map[i] = check_capitalized(tok_map[i], og_map[i])
                line.append(punct_map[i]['resolved'])

            else:
                line.append(punct_map[i]['raw_token'])

        else:
            line.append(punct_map[i])

    try:
        line = re.sub('<space>', ' ', ''.join(line))
    except:
        print('line 189')
        print(line[140:150])
        for idx, i in enumerate(line):
            if i == None:
                print(idx)
            
        #print(line)
    try:
        line = re.sub(r'``', '"', line)
    except:

        print('200 ' + line)
    line = re.sub(r"''", '"', line)
    #line = re.sub('a a-', 'a-', line)

    if last_method:

        line = fix_lonely_prefix(line)
        line = re.sub("'an", 'an', line)
    # why did you take this out!
    line = twobecomeone(line)
    line = re.sub('  ', '', line)

    return line


def decode_rule(topkey, rule):
    splitkey = topkey.split('/')

    if len(splitkey) > 1:

        return splitkey

    else:

        return topkey


def diacritic_normaliser(token):

    goc_vowels = {
        'á': 'à',
        'é': 'è',
        'í': 'ì',
        'ó': 'ò',
        'ú': 'ù',

        'Á': 'À',
        'É': 'È',
        'Í': 'Ì',
        'Ó': 'Ò',
        'Ú': 'Ù',
    }

    split_tok = [i for i in token]

    for idx, tok in enumerate(split_tok):

        if tok in goc_vowels:
            split_tok[idx] = goc_vowels[tok]

    return ''.join(split_tok)


def fetch_text(path):
    return [i for i in open(path).read().splitlines() if i != '']


def find_shared_keys(conditions, ngram, rule_conditions):
    for key in conditions.keys():

        if key in ngram and ngram[key] != None:

            if ngram[key]['raw_token'] == conditions[key]['raw_token']:
                rule_conditions[key] = True

    return rule_conditions


def fix_white_space(line):
    line = line.split(' ')
    line = [i for i in line if i != '']
    return ' '.join(line)


def hyphenated_norm(raw_token, normaliser=None):
    """
    Splits hyphenated words and tries to normalise
    each token individually
    """

    individual_tokens = raw_token.split('-')

    resolved_tok = []

    for i in individual_tokens:
        
        lookup = normaliser.lexicon.lexicon_lookup(i)

        if lookup == 'gaelic_words':
            resolved_tok.append(i)
            continue
        else:
            
            lookup = normaliser.rule_lookup(i, ignore_rule=hyphenated_norm)

        if lookup:

            if lookup['lexicon'] in ['trad_lexicon', 'misspelt_lexicon']:
                resolved_lookup = normaliser.lexicon.resolve_token(lookup['resolved'], lookup['lexicon'])
                resolved_tok.append(resolved_lookup)

            elif lookup['lexicon'] == 'english_words':
                resolved_tok.append(i)

            elif lookup['lexicon'] == 'gaelic_words':
                resolved_tok.append(i)
        else:
            resolved_tok.append(i)

    resolved = '-'.join(resolved_tok)

    # if len(resolved_tok) > 1:
    #     if not normaliser.lexicon.lexicon_lookup(resolved) and len(resolved_tok[0]) > 2 and len(resolved_tok[1]) > 2:
    #         """
    #         Avoiding false positives with affixed tokens
    #         """
    #
    #         resolved = ' - '.join(resolved_tok)

    if resolved != raw_token:

        return {'resolved': resolved,
                'lexicon': 'gaelic_words',
                'rule': hyphenated_norm.__name__}
    else:
        return None


def init_ngram():
    ngrams = {

        'ngram_02': {'raw_token' : 'None'}, 
        'ngram_01': {'raw_token' : 'None'},
        'ngram': {'raw_token' : 'None'},
        'ngram_1':{'raw_token' : 'None'},
        'ngram_2': {'raw_token' : 'None'},
    }

    return ngrams


def lemm_lookup(token, normaliser):
    stem = ps.stem(token)

    if normaliser.lexicon_lookup(stem):
        return True


def lower_lookup(raw_token, normaliser):
    """
    This rule alternates between a lowered/capitalised/stemmed version
    of a token to see if the processed version is in the lexicon.
    """

    token = remove_punct_1(raw_token)
    tokens = [token.lower(), token.capitalize(), token.upper(), ps.stem(token.lower())]

    for token in tokens:

        lookup = normaliser.lexicon.lexicon_lookup(token)

        if lookup:

            if check_capitalised(raw_token):
                return {'resolved': token.capitalize(),
                        'lexicon': lookup,
                        'rule': lower_lookup.__name__}
            else:

                return {'resolved': token,
                        'lexicon': lookup,
                        'rule': lower_lookup.__name__}

    return None


def multigram_rule_check(rule, topkey, ngram):
    rule_matches = []

    rule_conditions = {i: False for i in topkey}

    multitopkey = '/'.join(topkey)

    for i in rule[multitopkey]:

        for matches in rule[multitopkey][i]:

            match = matches.split(' ')
            condish = {}

            for x, y in zip(match, topkey):
                condish[y] = {'raw_token': x}
            rule_matches.append(condish)

    for conditions in rule_matches:

        rule_conditions = find_shared_keys(conditions, ngram, rule_conditions)

        if rule_conditions == {i: True for i in topkey}:
            return True

        else:
            rule_conditions = {i: False for i in topkey}


def output_text(path, normalised_text):
    with open(path, 'w') as file:
        for line in normalised_text:
            file.write('{}\n'.format(line))


double_space = re.compile('  ')
all_apostrophes = re.compile(r"[’'`‘']")
all_hyphens = re.compile("[‒–—―]")


def pre_process_raw_text(line):
    line = space_reduce(line)
    line = re.sub(all_apostrophes, "'", line)
    line = re.sub(bad_comma, "' ,\"", line)
    line = re.sub(all_hyphens, '-', line)
    line = pre_fix_regex(line)
    line = re.sub(double_space, ' ', line)

    return line

def fetch_maps(line, return_toks=None, method_num=None):
    '''
    Do preprocessing ONCE!
    
    '''

    line = line.split(' ')
    line = ' <space> '.join(line)
    # line = line.split(' ')
    # for idx, tok in enumerate(line):
        
    #     if re.match(r'[\w-]+[,\".?!]+', tok):

    #         chars = ''.join(re.findall('\w-', tok))
    #         punct = ''.join(re.findall('[^\w-]', tok))
    #         line[idx]=chars
    #         line.insert(idx+1, punct)

    # line=' '.join(line)

    punct_toks = []



    for i in line.split(' '):

        if i == '<space>':
            punct_toks.append([i])
            continue

        punct_toks.append(word_tokenize(i))

    token_line_map, punct_map = punct_line_map(punct_toks)
    if return_toks:
        return list(token_line_map.values())

    #print(punct_map, token_line_map)

    return punct_map, token_line_map


def process_topkey(topkey):

    splitkey = topkey.split('/')
    if len(splitkey) > 1:

        return splitkey
    else:
        return topkey


def punct_line_map(lists):
    line_map = {}
    no_punct_line_map = {}
    idx = 0

    apostroph_tok = re.compile("[’'][a-zA-Z]+"
                               "|'[a-z]"
                               "|[a-z]'"
                               "|a-zA-Z]+[’']["
                               "|[a-z]?-?[a-zA-Z]+[’']"
                               "|[a-z]+-?[a-zA-Z]+[’']"
                               "|[a-zA-Z]+['’][a-zA-Z]+"
                               )

    """
    Double check an-dràsta' is not being tokenized properly 
    ROB!
    """
    for i in lists:

        if re.match(apostroph_tok, ''.join(i)):
            line_map[idx] = ''.join(i)
            idx += 1
            continue

        for toks in i:

            if toks in punctuation or toks == '<space>':

                no_punct_line_map[idx] = toks
                idx += 1

            else:
                line_map[idx] = toks
                idx += 1

    return line_map, no_punct_line_map


def remove_hyphen(raw_token, normaliser):
    """
    A lot of words are separated by a hyphen, this code checks to see if
    the token exists in the lexicon as a bigram
    """
    if not re.match('-', raw_token):
        return None

    hyphen = re.compile('-')
    token = re.sub(hyphen, '', raw_token)

    lookup = normaliser.lexicon.lexicon_lookup(token)

    if lookup:
        try:

            resolved = normaliser.lexicon.resolve_token(token, lookup)
        except:
            print(token, lookup)
        return {'resolved': resolved,
                'lexicon': lookup,
                'rule': remove_hyphen.__name__}


def remove_punct_1(token):
    """
    Removes punctuation, however we may not need this
    as I have created rules to disambiguate tokens
    with trailing punctuation
    """

    punct = re.compile(r"[,\.\"\,,]")
    return re.sub(punct, '', token)


def replace_at_index(string, index, sub):
    string = [i for i in string]
    string[index] = sub
    return ''.join(string)


def restore_space(line):
    return re.sub('<space>', ' ', line)


def rule_check(rule, ngram, verbose=None):

    pre_topkey, replace_with = top_key(rule)

    topkey = process_topkey(pre_topkey)

    if type(topkey) == list:

        rule_conditions = multigram_rule_check(rule, topkey, ngram)

        if rule_conditions == True:
            return rule['replace_with']
        else:
            return None

    rule_conditions = {i: False for i in list(rule[topkey].keys())}

    if not ngram[topkey]:

        #print('not ngram')
        return None

    try:
        ruletype = rule['type']
    except:
        ruletype = None
        print(rule)

    for condition in rule[topkey]:
        if condition == 'match':
            matches = {x: False for x in rule[topkey][condition]}

        for i in rule[topkey][condition]:

            if condition == 'match':

                if ruletype == 'regex':
 
                    if re.match(i, ngram[topkey]['raw_token']):

                        if verbose:
                            print('Match Found!')
                        rule_conditions[condition] = True

                    else:
                        continue

                elif ruletype == 'string' or ruletype == 'not_string':
                    if i == ngram[topkey]['raw_token']:
                        if verbose:
                            print('Match Found!')
                        rule_conditions[condition] = True

                    else:
                        continue

            elif condition == 'pos':

                try:

                    if fuzz.ratio(rule[topkey][condition], ngram[topkey]['pos']) > 50:
                        rule_conditions[condition] = True

                except KeyError:

                    '''
                    I seem to have a bug wherby the 
                    pos is stripped after analyse_line 
                    not really sure how it is doing it 
                    but oh well
                    '''
                    continue

    # if ruletype == 'not_string':
    #     print(rule_conditions)
    #     if rule_conditions == {i: False for i in rule_conditions.keys()}:
    #         return rule['replace_with']
    
    if rule_conditions == {i: True for i in rule_conditions.keys()}:

        return rule['replace_with']


def strip_prep(raw_token, normaliser):
    """
    This is similar to the above rule except it is looking
    for a suffix that is seperated by an apostrophe.
    """

    suffix = re.compile(r"dh+'\"")
    if not re.match(suffix, raw_token):
        return None
    token = re.sub(suffix, '', raw_token)

    lookup = normaliser.lexicon.lexicon_lookup(token)

    if lookup:
        return {'resolved': raw_token,
                'lexicon': lookup,
                'rule': strip_prep.__name__}
    return None


def strip_suffix(raw_token, normaliser):
    """
    THIS IS NAMED WRONG
    A lot of tokens have an inflected suffix that acts as
    either a preposition or article. This rule strips the suffix
    to see if the root token is in the lexicon. If it is the original
    token is returned.
    """

    suffix = re.compile(r'\b[thdnb]+-')

    if re.match(suffix, raw_token):
        tok_suffix=re.findall(suffix, raw_token)[0]

    else:
        tok_suffix=''

    token = re.sub(suffix, '', raw_token)

    if token == raw_token:
        return None

    lookup = normaliser.lexicon.lexicon_lookup(token)
    rule_lookup = normaliser.rule_lookup(token)

    if rule_lookup:
        lookup = normaliser.lexicon.lexicon_lookup(rule_lookup['resolved'])
        
        if lookup:

            return {'resolved': tok_suffix + rule_lookup['resolved'],
                    'root': token,
                    'lexicon': lookup,
                    'rule': strip_suffix.__name__}
    elif lookup:
        return {'resolved': raw_token,
                    'root': token,
                    'lexicon': lookup,
                    'rule': strip_suffix.__name__}
    return None


def swap_vowels(raw_token, normaliser, verbose=None):
    token = [i for i in raw_token]
    goc_vowels = {
        'e': 'è',
        'a': 'à',
        'i': 'ì',
        'o': 'ò',
        'u': 'ù',
        'A' : 'À',
        'E' : 'É',
        'I' : 'Ì',
        'O' : 'Ò',
        'U' : 'Ù'
    }

    flip_direction = {
        'é': 'è',
        'á': 'à',
        'í': 'ì',
        'ó': 'ò',
        'ú': 'ù',
        'Á' : 'À',
        'É' : 'É',
        'Í' : 'Ì',
        'Ó' : 'Ò',
        'Ú' : 'Ù'
    }

    for idx, i in enumerate(token):

        if i in goc_vowels:
            token[idx] = goc_vowels[i]

        if i in flip_direction:
            token[idx] = flip_direction[i]

        vow_swapped = ''.join(token)

        if vow_swapped == raw_token:
            continue

        lookup = normaliser.lexicon.lexicon_lookup(vow_swapped, verbose)

        if lookup and vow_swapped != raw_token:

            if lookup in ['trad_lexicon', 'misspelt_lexicon']:

                return {'lexicon': lookup,
                        'resolved': normaliser.lexicon.resolve_token(vow_swapped, lookup),
                        'rule': swap_vowels.__name__}

            return {'lexicon': lookup,
                    'resolved': vow_swapped,
                    'rule': swap_vowels.__name__}

        token = [i for i in raw_token]

    return None


def remove_grave(raw_token, normaliser, verbose=None):
    remove_vowel = {
        'è': 'e',
        'à': 'a',
        'ì': 'i',
        'ò': 'o',
        'ù': 'u',
        'é': 'e',
        'á': 'a',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
    }

    splat_token = [i for i in raw_token]  #

    for idx, character in enumerate(splat_token):

        if character in remove_vowel:
            try:

                splat_token[idx] = remove_vowel[character]
            except:
                continue

            removed = ''.join(splat_token)

            lookup = normaliser.lexicon.lexicon_lookup(removed)

            if lookup:
                if lookup in ['trad_lexicon', 'misspelt_lexicon']:

                    return {'lexicon': lookup,
                            'resolved': normaliser.lexicon.resolve_token(removed, lookup),
                            'rule': remove_grave.__name__}

                else:

                    return {'lexicon': lookup,
                            'resolved': removed,
                            'rule': remove_grave.__name__}

            else:
                splat_token = raw_token.split()

    return None

def token_match(line, match):
    if re.search(match, line):
        return True
    else:
        return None


def top_key(dic):
    try:
        keys = list(dic.keys())
        return keys[0], keys[1]
    except:
        print(dic)


def twobecomeone(line):
    twobecomebefore = re.compile(r' 2become1')
    twobecomeafter = re.compile(r'2become1 ')
    twobecomeinbetween= re.compile('2become1')

    line = re.sub(twobecomebefore, '', line)
    line = re.sub(twobecomeafter, '', line)
    line = re.sub(twobecomeinbetween, '', line)

    return line


ool_rules = [swap_vowels,
             strip_suffix,
             remove_hyphen,
             strip_prep,
             lower_lookup,
             remove_grave,
             add_hyphen,
             hyphenated_norm,
             consonant_swap]
             #add_last_vowel]

punctuation = [i for i in punctuation]
for idx, i in enumerate(punctuation):
    if i == "'":
        del punctuation[idx]

punctuation = ''.join(punctuation)