from nltk.corpus import words
import pickle, pandas as pd, re, os
from tqdm.auto import tqdm
from Levenshtein import distance
import datetime

def fetch_dictionaries(lexicon_path):
    
    print('Loading Lexicon from {}'.format(lexicon_path))

    lexicons = {}
    for i in tqdm(sorted(os.listdir(lexicon_path)), desc='Reading Lexicon'):
        
        try:
            lexicons[i[:-4]] = pickle.load(open('{}{}'.format(lexicon_path,i), 'rb'))
        except:
            continue
            print('{}{}'.format(lexicon_path,i))
    
    return lexicons

'''
The Lexicon class loads and stores the lexicons that are exported and processed
from Michael Baur's online Scottish Gaelic Dictionary. There are 4 lexicons loaded:
- Traditional Spellings: The traditional spellings mapped to their GoC forms
- Misspelt Words: Misspellings mapped to correct spellings
- English Words: List of English words from corpus
- Gaelic Words: Correctly spelt GoC Gaelic 
The lexicon is used to try and match a token to a lexicon. If the token is matched to any
lexicon apart from the Gaelic Words then the correct spelling, if present, if added 
to the tokens meta data. 
'''
class Lexicon:

    def __init__(self, lexicon_path):

        self.lexicon_path = lexicon_path
        self.lexicons = fetch_dictionaries(lexicon_path)
        self.added = []
        self.deleted = []
        self.custom_lexicon= {}

    def lexicon_lookup(self, raw_token, verbose=None):

        '''
        This function takes a string token and, for each lexicon that is loaded
        in the lexicon object, looks up the token. Depending on which lexicon it is found 
        in depends on the next action. The function returns a string that tells the user
        where the token is found for debugging.
        args: 
            token: String that is a tokenesied word from the input text
            verbose: Can be anything, if present the lexicon name is printed to user
        returns:
            string if token in lexicon 
            None if token not present 
        '''

        lowered = raw_token.lower()

        for token in [raw_token, lowered]:
            
            '''
            The order of lookup is important to avoid taggin a Gaelic word
            as an english one. 
            '''
            if token in self.lexicons['gaelic_words']:

                # gaelic_words is a pickled python dictionary containing all 
                # correctly spelled gaelic words 

                if verbose:
                    print(verbose)
                    print('Token in Lexicon')
                return 'gaelic_words'

            elif token in self.lexicons['misspelt_lexicon']:
                
                # misspelt lexicon is a pickled python dictionary mapping commonly 
                # misspelt words and their correct spelings

                if verbose:
                    print('Misspelt Token')
                return 'misspelt_lexicon'

            elif token in self.lexicons['trad_lexicon']:

                # same as misspelt, there is a mapping from traditional to correct spelling

                if verbose:
                    print('Traditional Spelling')
                return 'trad_lexicon'    

            elif token in self.lexicons['english_words']:
                
                # token is present in a pickled list of english words

                if verbose:
                    print('English')
                return 'english_words'

            elif token in self.lexicons['custom_lexicon']:
                if verbose:
                    print('custom')
                return 'custom_lexicon'

        if verbose:
            print('Not in Lexicon')

        return None 

    def lookup_token(self, token):

        for lex in self.lexicons.keys():
            if token in self.lexicons[lex]:
                return lex

        return None 

    def resolve_token(self, token, lexicon_found):
        
        '''
        There are multiple 'correct' forms of words in the lexicon. This script 
        tries to match the correct spelling by measuring the edit distance
        '''

        distances = []

        if lexicon_found in ['english_words', 'custom_lexicon' , 'gaelic_words']:
            return token

        if token in self.lexicons[lexicon_found].keys():
            for i in self.lexicons[lexicon_found][token]['correct_spelling']:

                distances.append((distance(token, i), i))
    
        elif token.lower() in self.lexicons[lexicon_found].keys():

            for i in self.lexicons[lexicon_found][token.lower()]['correct_spelling']:
    
                distances.append((distance(token.lower(), i), i))
        
        else:
            return token
    
        try:
            return min(distances)[1]
        except:
            return token

    def add2lexicon(self, lexicon_name, token, mapping):

        # Tokens can be added to the dictionaries ad hoc

        
        if token in self.lexicons[lexicon_name]:

            print('Token already in lexicon')

        print(f'Adding {token} to {lexicon_name}')

        self.lexicons[lexicon_name][token] = mapping
        self.added.append((lexicon_name, token))

    def delete_frm_lexicon(self, lexicon_name, token):

        # words can also be deleted from the lexicon


        try:
            del self.lexicons[lexicon_name][token]
            print('Deleted {} from {}'.format(token, lexicon_name))
            self.deleted.append((lexicon_name, token))
        except:
            print('token not in lexion')
                  
    def save_lexicon(self, lexicon_name):

        # The lexicon can be updated, maybe useful for an interface
        
        lexicon_path = '{}{}.pkl'.format(self.lexicon_path, lexicon_name)
        with open(lexicon_path, 'wb') as file:
            pickle.dump(self.lexicons[lexicon_name], file)
        print('Updated {} Lexicon'.format(lexicon_name))

        with open(f'{self.lexicon_path}lexicon_changes.txt', 'a+') as file:

            file.write(f'\n{str(datetime.datetime.now())}\n')

            if self.added:
                file.write('\nAdded To Lexicon\n\n')
                for lexicon, token in self.added:
                    file.write('{} - {}\n'.format(token, lexicon))

            if self.deleted:
                file.write('\nDeleted From Lexicon\n\n')
                for lexicon, token in self.deleted:
                    file.write('{} - {}\n'.format(token, lexicon))

        