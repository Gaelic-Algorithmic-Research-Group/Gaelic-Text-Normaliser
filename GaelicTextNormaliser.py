import argparse as ap
import pickle

import pandas as pd
import yaml
import Levenshtein
from diff_match_patch import diff_match_patch

from utils.regex_functions import RegexFunctions
from utils.text_normaliser import *
from utils.preprocess import preprocess_doc

from tqdm.auto import tqdm
from utils.lexicon import Lexicon
from hunspell import Hunspell

'''
The TextNormaliser is the main class and can be imported
or hosted on a server. A config file can be used to input 
the different paths to resources or can be declared ad hoc
args:
    from_config  :  This is the path to the config file. Can be a string 
                  or the imported dictionary. If config is present it is 
                  not necessary to fill in the rest of the args.
    lexicon_path : Path to the folder containing the lexicons
    model_path   : path to part of speech tagger model. Options are 
                   a simple tagger or more detailed.
    tagset       : path to tagset which contains deambiguated tags 
    ngram_rules  : path to yaml file containing the ngram rules 
    methods      : Methods for normalisation. So far there are two different methods
                   memory_based or ngram_based. Default config uses
                   both. Useful for testing if a method improves the 
                   accuracy
'''

h = Hunspell()
ool_rules = ool_rules
diff = diff_match_patch()
sc = Hunspell('gd_GB', hunspell_data_dir='dictionaries')


# sc = hunspell.HunSpell('dictionaries/gd_GB.dic', 'dictionaries/gd_GB.aff')

def mainargs():
    args = ap.ArgumentParser()
    args.add_argument('--path_to_config', type=str,
                      help="The config holds the predefined configuration for the normaliser",
                      default="config.yaml")
    args.add_argument('--path_to_input_text', type=str, help="Path to the text to be normalised")
    args.add_argument('--input_text', type=str, help="Input text in the command line to be normaliseed", default=None)
    args.add_argument('--output_path', type=str, help="Path for the outputted text")
    args.add_argument('--return_backend', type=str,
                      help="Return a backend file with further analysis of the normaliser", default=None)
    args.add_argument('--verbose', type=str, help="Print to screen info about normalisation (may slow down the program",
                      default=None)
    args = args.parse_args()

    return args


def multihyphen(token):
    splat_tok = token.split('-')

    if len(splat_tok) >= 2:

        if not sc.spell(token):
            return ' '.join(splat_tok), True

    return token, False


def paint_line(tok_map, token):

    for num, tok in tok_map.items():
        if tok == token:
            tok_map[num] = f'[!{token}!]'

    return tok_map, token


def save_text(text, path):
    """
    The text can be outputted to a defined
    path
    """

    if type(text) == str:
        text = text.split('\n')

    elif type(text) == list:
        text = text[0].split('\n')

    with open(path, 'w') as file:
        for i in text:
            file.write('{}\n'.format(i))

    print('File saved to {}'.format(path))


def top_key(dic):
    # Finds the first key of a dictionary

    keys = list(dic.keys())
    return keys[0], keys[1]


def load(path):
    # Finds path in config that is a yaml file

    if path[-4:] == 'yaml':
        return yaml.safe_load(open(path))

    return pickle.load(open(path, 'rb'))


class TextNormaliser:

    def __init__(self, from_config=None, lexicon_path=None,
                 model_path=None, tagset=None, ngram_rules=None,
                 methods=None, num_lines=None):

        self.ool_rules = ool_rules

        if from_config:
            self.load_config(from_config)

        if lexicon_path:
            self.lexicon = Lexicon(lexicon_path)

        if tagset:
            self.tagset = load(tagset)

        if model_path:
            self.loaded_model = job_load(model_path)

        if ngram_rules:
            self.ngram_rules = load(ngram_rules)

        if methods:
            self.methods = methods

        if num_lines:
            self.num_lines = num_lines

    def load_config(self, config=None):

        """
        args:
            config: either a dictionary or path to a yaml file
                    if the type is a dictionary the config can
                    be loaded in a dictionary environment
        returns: class variables are all set
        """

        if type(config) == str:
            print('Loading Config from {}'.format(config))
            config = yaml.safe_load(open(config))

        elif type(config) == dict:
            config = config

        self.lexicon = Lexicon(config['lexicon_path'])
        self.tagset = load(config['tagset'])
        self.loaded_model = job_load(config['model_path'])
        self.ngram_rules = load(config['ngram_rules'])
        self.methods = config['methods']
        self.regex_functioniser = RegexFunctions(config['regex_rules'])
        self.num_lines = config['num_lines']

    def set_defaults(self):

        # Default config for normaliser assuming download from github
        print('Loading Defaults')
        self.lexicon = Lexicon('GaelicTextNormaliser/static/lexicon/'),
        self.loaded_model = job_load('GaelicTextNormaliser/gd_model/gd_simple_model.sav'),
        self.tagset = pickle.load(open('GaelicTextNormaliser/tagset/tagset.pkl', 'rb'))
        self.ngram_rules = pickle.load(open('GaelicTextNormaliser/ngram_rules/rules.yaml'))

    def analyse_line(self, tok_map, just_tags=None, verbose=None):

        """
        args:
            tok_map: dictionary of tokens mapping to index in sentence
            verbose: prints the output from lexicon_lookup
        returns:
            for each token in tok_map the script attempts to find a lexicon
            that contains the token and if there is a GoCified spelling of the
            token it is resolved. Each token is represented by a dictionary
            that provides the result from the lookup and other meta data
        """

        analysed = {}
        for num, raw_token in tok_map.items():

            lookup = self.lexicon.lexicon_lookup(raw_token, verbose)

            if lookup:

                analysed[num] = {'raw_token': raw_token,
                                 'lexicon': lookup}

                if just_tags:
                    continue

                if lookup in ['trad_lexicon', 'misspelt_lexicon']:
                    analysed[num]['resolved'] = self.lexicon.resolve_token(raw_token, lookup)

                    continue

            else:

                analysed[num] = {'raw_token': raw_token,
                                 'lexicon': 'out_of_lexicon'}

                if just_tags:
                    continue

                '''
                If a token cannot be identified a few rules are performed to cancel out
                incorrect spelling or false negatives
                '''

                lookup = self.rule_lookup(raw_token)

                if lookup:
                    lookup['raw_token'] = raw_token
                    analysed[num] = lookup
                    continue

                else:

                    '''
                    If a token can't be found in a lexicon it is tagged as 
                    out of lexicon. The tag is helpful so that the token can
                    be processed later
                    '''
                    raw_token, fixed = multihyphen(raw_token)

                    analysed[num] = {'raw_token': raw_token,
                                     'lexicon': 'out_of_lexicon'}

        return analysed

    def extract_pos(self, line_map):

        """
        Parts of speech are added to the tokens from the loaded POS model.
        args:
            line_map: mappings of tokens to index in a line
            loaded_model
        returns:
            The code adds to the meta data the part of speech according
            to the model, this data can then be used to add constraints
            to the rule based normalisation. POS model is already loaded
            in memory.
        """
        line = []

        for i in line_map:

            try:
                line.append(line_map[i]['resolved'])
            except:
                line.append(line_map[i]['raw_token'])

        line = ' '.join(line)

        # simple tag inherited from Loïc's POS code

        pos_tagged = simple_tag(line, loaded_model=self.loaded_model)

        try:
            if pos_tagged[0].split('\n') == []:
                return line_map
        except:
            return line_map

        possed = pos_tagged[0].split('\n')

        for num, i in zip(line_map, possed):
            pos = i.split('\t')
            line_map[num]['pos'] = pos[-1]

        return line_map

    def rule_lookup(self, raw_token, ignore_rule=None, verbose=None):

        """
        The code iterates through varies lexical rules
        to make string level fixes to a token to try and place it in a lexicon
        some words may be missing a hyphen or other small feature. These
        rules do not take ngrams into account
        args:
            raw_token: raw token string
            verbose: prints if a rule is succesfull or not
        returns:
            returns the result of the lexicon lookup and adds the rule
            that identified the token to the meta data of the token
        """
        for rule in self.ool_rules:

            if ignore_rule:
                if rule.__name__ == ignore_rule.__name__:
                    continue

            lookup = rule(raw_token, normaliser=self)

            if verbose:
                print(rule.__name__)
                print(lookup)

            if lookup == 'english_words':
                # English Words are not processed
                continue

            if lookup:
                if lookup['resolved'] == raw_token:
                    continue
                try:
                    return lookup

                except:
                    print('poop')
                    print(raw_token)
                    continue

        return None

    def bigram_resolve(self, tik_map):

        """
        There are a few tokens that are indetifiable in the lexicon when they are
        looked up together. This code generates bigrams and looks up the bigram.
        args:
            tik_map: The token map that maps tokens to indexes in a line
        returns:
            The token map is returned with bigram resolved tokens resolved.
        """
        idxs = [i for i in tik_map.keys()]

        for num, i in enumerate(idxs):

            if num + 1 == len(idxs):
                break

            bigram_1_idx = idxs[num]
            bigram_2_idx = idxs[num + 1]

            '''
            Have a go adding another ngram in Rob
            
            '''

            bigram_1 = tik_map[bigram_1_idx]['raw_token']
            bigram_2 = tik_map[bigram_2_idx]['raw_token']

            bigram = '{} {}'.format(bigram_1, bigram_2)

            bigram_lookup = self.lexicon.lexicon_lookup(bigram)

            if bigram_lookup:

                if bigram_lookup in ['gaelic_words', 'english_words']:
                    continue

                elif bigram_lookup in ['trad_lexicon', 'misspelt_lexicon']:

                    """
                    'g a doesn't work because of this!
                    an da as well!
                    """

                    resolved = self.lexicon.resolve_token(bigram, bigram_lookup)
                    # print(bigram)
                    # print(resolved)
                    if len(resolved.split(' ')) == 2:
                        tik_map[bigram_1_idx]['resolved'] = resolved.split(' ')[0]
                        tik_map[bigram_2_idx]['resolved'] = resolved.split(' ')[1]

                    elif len(resolved.split(' ')) == 1:
                        # print(resolved.split(' '))
                        tik_map[bigram_1_idx]['resolved'] = resolved.split(' ')[0].strip()
                        tik_map[bigram_2_idx]['resolved'] = '<space>'

            # else:

            #     '''
            #     Some words can be resolved when they are joined on a hyphen
            #     this code cancels out any issues if a word is writted without 
            #     a hyphen but requires one
            #     '''

            #     bigram = '{}-{}'.format(bigram_1, bigram_2)
            #     bigram_lookup = self.lexicon.lexicon_lookup(bigram)

            #     if bigram_lookup:

            #         if bigram_lookup in ['gaelic_words', 'english_words']:
            #             continue

            #         else:

            #             resolved = self.lexicon.resolve_token(bigram, bigram_lookup)

            #             if len(resolved.split('-')) == 2:
            #                 tik_map[bigram_1_idx]['resolved'] = resolved.split('-')[0]
            #                 tik_map[bigram_2_idx]['resolved'] = resolved.split('-')[1]

            #             elif len(resolved.split('-')) == 1:
            #                 tik_map[bigram_1_idx]['resolved'] = resolved.split('-')[0].strip()
            #                 tik_map[bigram_2_idx] = {'raw_token' : '<space>'}

        return tik_map

    def trigram_resolve(self, tik_map):

        """
        There are a few tokens that are indetifiable in the lexicon when they are
        looked up together. This code generates bigrams and looks up the bigram.
        args:
            tik_map: The token map that maps tokens to indexes in a line
        returns:
            The token map is returned with bigram resolved tokens resolved.
        """
        idxs = [i for i in tik_map.keys()]

        for num, i in enumerate(idxs):

            if num + 1 == len(idxs) or num + 2 == len(idxs):
                break

            trigram_1_idx = idxs[num]
            trigram_2_idx = idxs[num + 1]
            trigram_3_idx = idxs[num + 2]

            '''
            Have a go adding another ngram in Rob
            I'm Trying!
            '''

            trigram_1 = tik_map[trigram_1_idx]['raw_token']
            trigram_2 = tik_map[trigram_2_idx]['raw_token']
            trigram_3 = tik_map[trigram_3_idx]['raw_token']

            trigram = '{} {} {}'.format(trigram_1, trigram_2, trigram_3)

            trigram_lookup = self.lexicon.lexicon_lookup(trigram)

            if trigram_lookup:

                if trigram_lookup in ['gaelic_words', 'english_words']:
                    continue

                elif trigram_lookup in ['trad_lexicon', 'misspelt_lexicon']:

                    """
                    'g a doesn't work because of this!
                    an da as well!
                    """
                    resolved = self.lexicon.resolve_token(trigram, trigram_lookup)

                    if len(resolved.split(' ')) == 3:
                        tik_map[trigram_1_idx]['resolved'] = resolved.split(' ')[0]
                        tik_map[trigram_2_idx]['resolved'] = resolved.split(' ')[1]
                        tik_map[trigram_3_idx]['resolved'] = resolved.split(' ')[2]

                    if len(resolved.split(' ')) == 2:
                        tik_map[trigram_1_idx]['resolved'] = resolved.split(' ')[0]
                        tik_map[trigram_2_idx]['resolved'] = resolved.split(' ')[1]
                        tik_map[trigram_3_idx]['raw_token'] = '<space>'

                    elif len(resolved.split(' ')) == 1:
                        tik_map[trigram_1_idx]['resolved'] = resolved.split(' ')[0].strip()
                        tik_map[trigram_2_idx]['raw_token'] = '<space>'
                        tik_map[trigram_3_idx]['raw_token'] = '<space>'

        return tik_map

    def gen_ngrams(self, tok_map, num, line_toks, line_idx, verbose=None):

        """
        The code creates a five key dictionary that includes the target token
        and the two ngrams either side.
        args:
            tok_map : tokens mapped to indexes
            num     : the index of the target token. This is so that the code knows
                    not to assign n - 1 if the target token is the first token in the line
                    avoiding index out of range error
            line_toks : list of only the indexes of the tokens in the line. Indexes of punctuation
                        are kept seperatly
            line_idx  : can't really remember why I have this in here.....
        returns:
            The code updates the meta data of a line of token mappings if a match
            is found in the handwritten rules
        """

        # initialise an empty dictionary of ngram mappings

        ngrams = init_ngram()

        if num > 1:
            ngrams['ngram_02'] = line_toks[num - 2]
            ngrams['ngram_02']['tok_idx'] = line_idx[num - 2]

        if num > 0:
            ngrams['ngram_01'] = line_toks[num - 1]
            ngrams['ngram_01']['tok_idx'] = line_idx[num - 1]

        ngrams['ngram'] = line_toks[num]
        ngrams['ngram']['tok_idx'] = line_idx[num]

        if num < len(line_toks) - 1:
            ngrams['ngram_1'] = line_toks[num + 1]
            ngrams['ngram_1']['tok_idx'] = line_idx[num + 1]

        if num < len(line_toks) - 2:
            ngrams['ngram_2'] = line_toks[num + 2]
            ngrams['ngram_2']['tok_idx'] = line_idx[num + 2]

        if verbose:
            print(ngrams)

        ngram_lookup = self.ngram_rule_lookup(ngrams)

        if ngram_lookup == 'Fail':
            return 'fail'

        if ngram_lookup:

            if type(ngram_lookup) == str:
                tok_map[line_idx[num]]['resolved'] = ngram_lookup

            elif type(ngram_lookup) == dict:

                resolved = getattr(self.regex_functioniser, ngram_lookup['function'])(
                    ngrams[ngram_lookup['ngram']]['raw_token'])

                tok_map[ngrams[ngram_lookup['ngram']]['tok_idx']]['resolved'] = resolved

        return tok_map

    def ngram_rule_lookup(self, ngrams, verbose=None):

        """
        This code tries to find a rule from the loaded rules
        if a match is found the lookup is return
        args:
            ngrams: A dictionary of 5 ngrams
        returns:s
            If no match is found the code returns None otherwise
            the resolved token meta data is returned
        """

        token = ngrams['ngram']['raw_token']

        tokens = [token, token.lower(), token.capitalize()]

        for tok in tokens:

            if tok in self.ngram_rules:

                if verbose:
                    print('Match')
                    print(token)

                for i in self.ngram_rules[tok]['rules']:

                    rule_lookup = rule_check(i, ngrams)

                    if rule_lookup:
                        return rule_lookup

    def ngram_based(self, line, return_backend=None, verbose=None, last_method=None):

        """
        This is the main function for the ngram based lookup also knows as
        rule-based. The rules are written in the rule file that can be found in the
        static folder. The function processed the line by extracting the tokens
        and the punctuation. Then generates the different data types for the rule
        based lookup.
        args:
            line: the string that is being normalised
            return_backend: If True the code returns the meta data for each token
            verbose: For each function that is passed the verbose printing will be activated
        returns:
            The main function returns a normalised string.
        """

        # Apostrophes are normalised to be consistent to make matching more likely

        '''
        punc_map is a dictionary mapping allowed punctation to an index in the line
        this is so that punctuation is not lost due to the various lexical rules i've 
        written. 
        tok_map contains the tokenised tokens and their index in the line
        '''

        punc_map, tok_map = fetch_maps(line)

        analysed = self.analyse_line(tok_map, just_tags=True, verbose=verbose)
        analysed = self.extract_pos(analysed)

        # the index of the line and the token indexes are collected in lists

        line_idx = list(analysed.keys())
        line_toks = list(analysed.values())

        for num, tok in enumerate(line_toks):
            analysed = self.gen_ngrams(analysed, num, line_toks, line_idx, verbose)

        # for debugging the code can print the line of the text

        if analysed == 'fail':
            print(line)
            return None

        '''
        The token and punctuation maps are passed to a decoder to extract resolved 
        tokens and to put them back together. Some text fixes are also applied to
        fix and rules that have executed incorrectly.
        '''

        decoded = decode_maps(analysed, punc_map, tok_map, last_method=last_method)
        decoded = re.sub(all_apostrophes, "'", decoded)

        if not return_backend:
            return decoded

        else:
            return decoded, analysed

    def memory_based(self, line, return_backend=None, verbose=None, last_method=None):

        """
        Top function for memory based lookup. The text is preprocessed and then
        sent to the lookup algorithm to try and match tokens to lexicons
        """
        # Round 1

        punc_map, tok_map = fetch_maps(line)
        # print(punc_map, tok_map)
        # return 0/0
        analysed = self.analyse_line(tok_map, just_tags=None, verbose=verbose)

        analysed = self.bigram_resolve(analysed)
        analysed = self.trigram_resolve(analysed)
        try:
            analysed = self.extract_pos(analysed)

        except:
            raise Exception("Something went wrong with the POS tagger")

        decoded = decode_maps(analysed, punc_map, tok_map, last_method=last_method)

        if not return_backend:
            return decoded

        else:
            return decoded, analysed

    def regex_rule_based(self, line, return_backend=None, verbose=None, last_method=None):

        punc_map, tok_map = fetch_maps(line)

        analysed = self.analyse_line(tok_map, just_tags=True, verbose=verbose)
        analysed = self.extract_pos(analysed)

        # the index of the line and the token indexes are collected in lists

        line_idx = list(analysed.keys())
        line_toks = list(analysed.values())

        for num, tok in enumerate(line_toks):

            if tok['lexicon'] in ['out_of_lexicon', 'gaelic_words']:
                resolved, rulename = self.regex_functioniser.rule_match(self, tok['raw_token'])

                if resolved:
                    line_toks[num]['resolved'] = resolved
                    line_toks[num]['rule'] = rulename

        decoded = decode_maps(analysed, punc_map, tok_map, last_method=last_method)
        decoded = re.sub(all_apostrophes, "'", decoded)

        if not return_backend:
            return decoded

        else:
            return decoded, analysed

    def spellchecker_based(self, line, return_backend=None, verbose=None, last_method=None):

        punc_map, tok_map = fetch_maps(line)
        analysed = self.analyse_line(tok_map, just_tags=None, verbose=verbose)

        for idx in analysed:

            if analysed[idx]['lexicon'] != 'gaelic_words':

                distances = []

                for token in sc.suggest(analysed[idx]['raw_token']):
                    distances.append((token, Levenshtein.distance(analysed[idx]['raw_token'], token)))

                if len(distances) > 1:
                    highest_match = sorted(distances, key=lambda x: x[1])[0][0]
                    analysed[idx]['resolved'] = highest_match

        decoded = decode_maps(analysed, punc_map, tok_map, last_method=last_method)

        if not return_backend:
            return decoded

        else:
            return decoded, analysed

    def normalise_doc(self, doc=None, doc_path=None, print_backend=None, return_backend=None, verbose=None):

        """
        Top function for normaling entire texts or line of texts. This function can
        be used inside a notebook to normalise from a path or from a string inside
        the notebook.
        args:
            doc_path: path to a txt file to be normalised
            doc: string to be normalised
            return_backend: returns a list that contains the meta data for each line
        returns:
            returns a string that is the normalised text and a list
            containing the backends of each line
        """
        normalised = []
        doc_backend = []

        if doc_path:
            doc = fetch_text(doc_path)
            # print(doc)
            doc = open(doc_path).read()
            pre_processed_doc = preprocess_doc(doc)
            pre_processed_doc = [i for i in pre_processed_doc.split('\n') if i != '']
            # print(pre_processed_doc)
            disable = False
        else:
            pre_processed_doc = [preprocess_doc(doc)]
            disable = True

        idx = 0

        for line in tqdm(pre_processed_doc, desc='Normalising Doc', disable=disable, total=self.num_lines):

            # code iterates through each method that is specified in the config

            for meth, method in enumerate(self.methods):

                if return_backend:
                    if meth == len(self.methods) - 1:

                        normalised_line, backend = getattr(self, method)(line, return_backend=return_backend,
                                                                         verbose=verbose, last_method=True)
                    else:
                        normalised_line, backend = getattr(self, method)(line, return_backend=return_backend,
                                                                         verbose=verbose)

                    if print_backend:
                        print(f'\nMethod: {method}\n')
                        for i in backend.values():
                            print(i)

                else:

                    if meth == (len(self.methods) - 1):

                        normalised_line = getattr(self, method)(line, return_backend=return_backend,
                                                                verbose=verbose, last_method='last line!')
                    else:
                        normalised_line = getattr(self, method)(line, return_backend=return_backend,
                                                                verbose=verbose)

                line = normalised_line

            normalised.append(line)

            if return_backend:
                doc_backend.append(backend)

            idx += 1

            if idx == self.num_lines:
                break

        if return_backend:
            return '\n'.join(normalised), doc_backend

        else:

            return '\n'.join(normalised)

    def tag_to_english(self, tag):

        # translates abbreviated pos tags
        return self.tagset[tag]

    def backendtable(self, backend):

        """
        For the webapp the backend can be transformed into
        an html table
        """
        df = pd.DataFrame(data=backend)
        df = df.fillna(' ').T
        df = df.reset_index()
        df = df.drop(columns='index')

        return df.to_html()

    def norm_diff(self, line, normalised):

        """
        Using Google's diff script the to pen creates a diff
        of the pre and post normalised file and turns it into
        pretty html
        """

        diffs = diff.diff_main(line, normalised)
        return diff.diff_prettyHtml(diffs)


if __name__ == '__main__':

    normargs = mainargs()
    normaliser = TextNormaliser(from_config=normargs.path_to_config)
    normalisd_text = None
    normargs.input_text = 'Ciamar a tha thu'

    if normargs.path_to_input_text:
        normalised_text = normaliser.normalise_doc(normargs.input_text)

    if normargs.input_text:
        normalised_text = normaliser.normalise_doc(doc=normargs.input_text)
        print(normalised_text)

    if normargs.output_path and normalised_text:
        save_text(normalised_text, normargs.output_path)

    if normargs.verbose and normalised_text:
        print(normalised_text)
