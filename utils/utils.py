import pandas as pd, re, os, pickle
from tqdm.auto import tqdm
from nltk.corpus import words

def fetch_text(path):
    return [i for i in open(path).read().splitlines() if i != '']
    
def clean_token(token):
    
    patterns = re.compile("[\.£$*\",”\(\)\[\]!:“&;?˩˧]+"  # Punctuation
                          "|<eng>|<gai>"                   # language tags
                          "|[$£]\d+\.\d+"                  # Currency
                          "| '\w' "                        # Words in quotes   
                          
                      )                                                
    fix_hyphenated = re.compile(r'[a-z]+- [a-z]+')
    for i in re.findall(fix_hyphenated, token):
        fixed = re.sub(' ','', i)
        token = re.sub(i, fixed, token)
        
    token = re.sub(patterns, '',token) 
    token = re.sub(r'\n', ' ',token) # white space markers
    token = re.sub(r'\s+', ' ',token) # double spacing
    return token

def clean_text(text):
    punct = re.compile(r'[,\.:"˩˧]')
    double_white_space = re.compile(r'\s+')

    return [re.sub(double_white_space,' ', (re.sub(punct, '', i))).lower() for i in text if i != '']

def token_tracker(line):
    return {idx : token for idx, token in enumerate(line.split(' '))}

def remove_mac_titles(mac_text):
    return [i for i in mac_text if i != ""][1::2]

def capture_numbers(token):
    numbers = re.compile(r'\d+')
    return re.match(numbers, token)

def load_dictionary(df, lexicon_set):
    
    lexicon_raw = sorted([i for i in df[lexicon_set].tolist() if type(i) != float and i != ' '])
    
    lexicon = []
    
    for i in tqdm(lexicon_raw, desc="Counting Tokens"):
        if type(i) != float:
            lexicon += [i.strip() for i in i.split(',')]
    
    lexicon_dic = {tok.lower() : idx for idx, tok in enumerate(sorted(set(lexicon)))}
    return lexicon_dic

def fetch_dictionaries(lexicon_path):
    
    print('Loading Lexicon from {}'.format(lexicon_path))
    lexicons = {}
    for i in tqdm(sorted(os.listdir(lexicon_path)), desc='Reading Lexicon'):
        
        lexicons[lexicon_name[:-3]] = pickle.load(open('{}{}'.format(lexicon_path,i)))
    
    return lexicons

def fetch_pos(df, pos, lexicon, exceptions):
    
    '''
    From Michael's database search for tokens based on pos
    '''
    
    adverbs = []

    for i in tqdm(range(len(df)), total=len(df)):
        
        try:
            
            if df.loc[i]['WordClassMerged'] == pos:
                if df.loc[i][lexicon][:3] in exceptions or df.loc[i][lexicon][:2] in exceptions:
                    adverbs+= [i.strip() for i in df.loc[i][lexicon].split(',') if i != '']
        except:
            continue
            
    return [i for i in adverbs if i != '']

def output_pos_list(path, pos_list):
    
    with open(path, 'w') as file:
        for i in pos_list:
            file.write(i)
            file.write('\n')

def line_checker(line, lexicon_dic, misspelt_dictionary, traditional_spelling,english_lexicon):

    token_map = []
    tokens = line.split(' ')

    for token in tokens:

        if token_lookup(token, lexicon_dic) == False:

            # token is not in correct spelling lexicon

            if token in misspelt_dictionary:
                token_map.append((token, 'misspelt'))
            
            elif token in traditional_spelling:
                token_map.append((token, 'trad'))

            elif capture_numbers(token) != None:
                token_map.append((token,'number'))
            elif token in english_lexicon:
                token_map.append((token,'english'))
            else:
                token_map.append((token,'bad'))

        else:
            # Token is in lexicon
            token_map.append((token,'fine'))

    return token_map

def bigrams_to_string(bigrams):
    line = []
    
    for i in bigrams:
        line.append(i[0])
        line.append(i[1])
        break
        
    for i in bigrams[1:]:
        line.append(i[1])
        
    return ' '.join(line)

def trigrams_to_string(trigrams):
    line = []
    
    for i in trigrams:
        line.append(i[0])
        line.append(i[1])
        line.append(i[2])
        break
    for i in trigrams[1:]:
        line.append(i[2])
    
    return ' '.join(line)

def html_line_checker(text, lexicon_dic, misspelt_dictionary, traditional_spelling,english_lexicon):

    token_map = []
    
    for line in text:
        
        token_lines = []
        tokens = line.split(' ')
        
        for token in tokens:

            if token_lookup(token, lexicon_dic) == False:

                # token is not in correct spelling lexicon

                if token in misspelt_dictionary:
                    token_lines.append(('<span style="background-color: blue;">{}</span>'.format(token)))

                elif token in traditional_spelling:
                    token_lines.append(('<span style="background-color: green;">{}</span>'.format(token)))

                elif capture_numbers(token) != None:
                    token_lines.append(('<span style="background-color: brown;">{}</span>'.format(token)))
                elif token in english_lexicon:
                    token_lines.append(('<span style="background-color: purple;">{}</span>'.format(token)))
                else:
                    token_lines.append(('<span style="background-color: red;">{}</span>'.format(token)))

            else:
                # Token is in lexicon

                token_lines.append(token)
                
        token_map.append(' '.join(token_lines))

    return '<br>'.join(token_map)

def fetch_tokens(tok_map):

    return list(tok_map.keys())

def save_text(text, path):
    with open(path, 'w') as file:
        for i in text.split('\n'):
            file.write('{}\n'.format(i))