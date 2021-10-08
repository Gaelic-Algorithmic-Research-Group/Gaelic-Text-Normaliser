import re
import yaml
import pickle

slender = ['e', 'i', 'è', 'ì', 'E', 'I', 'È','Ì']
broad = ['a', 'o', 'u', 'à', 'ò', 'ù', 'A', 'O', 'À', 'Ò', 'Ù', 'U']
vowels = ['a', 'e', 'i', 'o', 'u', 'à', 'è', 'ì', 'ò', 'ù', 'A', 'E', 'I','O', 'U', 'À','È','Ì','Ò','Ù']
len_cons = re.compile('[bcdgmpst]h')

sg_prefix = re.compile(r'[thna]-')
fh_or_vowel = re.compile(r"fh"
                          "|^Fh"
                          "|[aeiouAEIOUÀÈÌÒÙàèìòùéÉóÓáÁ]")

fhv_or_vowel = re.compile(r"[Ff]h[aeiouAEIOUÀÈÌÒÙàèìòùéÉóÓáÁ]"
                          "|[aeiouAEIOUÀÈÌÒÙàèìòùéÉóÓáÁ]"
                          )

cons_list_lenited = re.compile(r"'bh"
                                "|'ch"
                                "|'dh"
                                "|'gh"
                                "|'mh"
                                "|'ph"
                                "|'sh"
                                "|'th"
                                "|'fh")


def prefix_checker(token):
    if re.match(sg_prefix, token):
        return True

def check_capped(token):

    capped = token.capitalize()
    lowered = token.lower()

    if token == capped:
        return True 
    
    elif token == lowered:
        return False

class RegexFunctions():

    def __init__(self, path_to_rules):
        self.rules = self.load_rules(path_to_rules)
        self.adj_dic = pickle.load(open('static/ngram_rules/adverb_dic.pkl', 'rb'))
        self.verb_dic = pickle.load(open('static/ngram_rules/verb_dic.pkl', 'rb'))

    def load_rules(self, path_to_rules):

        return yaml.safe_load(open(path_to_rules))

    def adjective_lookup(self, token):
        
        if token[1:] in self.adj_dic:
            resolved = 'e {}'.format(token[1:])
            #print(resolved)
            return resolved

        else:
            return token

    def verbal_noun_lookup(self, normaliser, raw_token):

        token = raw_token

        is_capped = check_capped(raw_token)

        if token[0] == "'":
            token = token[1:]
        
        cap, lowered = token.capitalize(), token.lower()

        if cap in normaliser.regex_functioniser.verb_dic:
            token = cap
            
        elif lowered in normaliser.regex_functioniser.verb_dic:
            token = lowered

            if normaliser.regex_functioniser.verb_dic[token] in ['<Nv>', '<Nv--l>']:
                
                if re.match(fh_or_vowel, token):
                    
                    return raw_token[1:]

                elif re.match(len_cons, token):

                    return raw_token [1:]

                else:
                    
                    return "a' " + raw_token[1:]
                    
                   

        '''
        
        Import verb dictionary properly, each key can have more than one POS
        
        '''
        return "'" + token


    def initial_apostroph(self, normaliser, token):
    
        """
        Initial apostrophe word
        """

        if normaliser.lexicon.lexicon_lookup(token) != 'out_of_lexicon':
            return token
            
        if token[1:] in self.verb_dic:

            '''
            Word is a Verbal Noun
            '''
            
            if self.verb_dic[token[1:]] == '<Nv>' or self.verb_dic[token[1:]] == '<Nv--l>':

                
                """
                Word is a verbal noun
                """
                if re.match(fhv_or_vowel, token[1:][0]) or re.match(fhv_or_vowel, token[1:][:4]):

        
                    '''
                    Token begins with fh + vowel or a vowel
                    '''
                    
                    resolved = token[1:]
                    return resolved
                
            if re.match(cons_list_lenited, token[:3]):

                return f"a {token[1:]}"
            
            else:
                return f"a' {token[1:]}"
            
        if re.match(fhv_or_vowel, token[1]) or re.match(fhv_or_vowel, token[1:4]):

            resolved = token[1:]
            return resolved

        else:
            resolved = f"a {token[1:]}"
            return resolved

    def restore_vowel(self, normaliser, token):

        token_splat = [i for i in token]
        token_splat_vowels = [i for i in token if i in vowels or i == "'"]

        if token_splat_vowels[-2] in slender:
            token_splat[-1] = 'e'
        else:
            token_splat[-1] = 'a'

        resolved = ''.join(token_splat)

        lookup = normaliser.lexicon.lexicon_lookup(resolved)

        if lookup:
            return resolved
        else:

            if prefix_checker(resolved):
                lookup = normaliser.lexicon.lexicon_lookup(resolved[2:])

                if lookup:
                    return resolved

            return None

    def remove_inner_apostrophe(self, normaliser, token):

        no_apost = re.sub("'", "", token)

        if normaliser.lexicon.lexicon_lookup(no_apost):
            # print(f'Match: {no_apost}')
            return no_apost

        else:
            no_apost = re.sub("'", " ", token)

            token = self.bigram_lookup(normaliser, no_apost)

            if token:
                # print(f'Match: {token}')
                return token

            no_spaces = re.sub(' ', '', no_apost)
            token = self.split_token_lookup(normaliser, no_spaces)

            if token:
                # print(f'Match: {token}')
                return token

        return None

    def push_together(self, normaliser, token):

        token = re.sub(' ', '', token)
        return token

    def double_a(self, normaliser, token):

        token = re.sub('a a', 'a', token)
        return token

    def drop_last_a(self, normaliser, token):
        token = token[:-1]
        return token

    def rule_match(self, normaliser, token):

        rulename = 'nomatch'
        for i in self.rules:

            if re.match(i, token):

                resolved = getattr(self, self.rules[i])(normaliser, token)
                if resolved == token:
                    continue
                if resolved:
                    rulename = self.rules[i]
                    return resolved, rulename

        return None, rulename
        # why did you do this 

    def bigram_lookup(self, normaliser, bigram):

        bigrams = bigram.split(' ')

        if normaliser.lexicon.lexicon_lookup(bigrams[0]) and normaliser.lexicon.lexicon_lookup(bigrams[1]):
            return ' '.join(bigrams)
        else:
            return None

    def anam_fixer(self, normaliser, token):
       
        if token == "'n":
            return "an"
            
        elif token == "'m":
            return "am"

        else:
            return None

    def insert_space(self, normaliser, token):

        token = re.sub("'", "' ", token)
        return token

    def split_token_lookup(self, normaliser, token):

        splat_token = [i for i in token]
        attempt = splat_token

        for num in range(len(splat_token)):

            splat_token = [i for i in token]
            next_line = splat_token

            splat_token.insert(num, ' ')

            if num == 0:
                continue

            attempt = [normaliser.memory_based(i) for i in ''.join(splat_token).split(' ')]

            both_in_lexicon = {i: False for i in attempt}

            for i in attempt:

                if normaliser.lexicon.lexicon_lookup(i) == 'gaelic_words':
                    both_in_lexicon[i] = True

            if all(value == True for value in both_in_lexicon.values()):
                return ' '.join(attempt)

            splat_token.insert(num, splat_token[num + 1])

            if num == 0:
                continue

            attempt = [normaliser.memory_based(i) for i in ''.join(splat_token).split(' ')]

            both_in_lexicon = {i: False for i in attempt}

            for i in attempt:

                if normaliser.lexicon.lexicon_lookup(i) == 'gaelic_words':
                    both_in_lexicon[i] = True

            if all(value == True for value in both_in_lexicon.values()):
                #print(both_in_lexicon)
                return ' '.join(attempt)

    def apostroph2space(self,normaliser, token):

        if token[0] == 'b':

            token = re.sub("bh'", "bh' ", token)

        elif token[0] == 't':

            token = re.sub("th'", "th' ", token)
            
        return token
"""
"""