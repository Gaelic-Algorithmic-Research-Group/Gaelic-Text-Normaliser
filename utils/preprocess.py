import re
from nltk.stem import PorterStemmer
import string 

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
spaces = re.compile('  ')
upper = re.compile(r'[A-Z]')
double_space = re.compile('  ')
all_apostrophes = re.compile(r"[’'`‘'’]")

all_hyphens = re.compile("[‒–—―]")

def space_reduce(line):
    line = re.sub('\t', ' ', line)
    space_matches = re.findall(spaces, line)
    for match in space_matches:
        line = re.sub(spaces, ' ', line)
        
    return line 


def preprocess_doc(text):
    #print(text)
    text = space_reduce(text)
    all_apostrophes = re.compile(r"[’'`‘'’]")

    
    text = re.sub(all_apostrophes, "'", text)   # 
    
    text = re.sub(r"\bdh' ", "dh'", text)

    #a'word > a' word / a'mhìos but problem words like: a's
    text = re.sub(r"\bb-", "b' ", text)
    text = re.sub(r"\bd-", "d' ", text)
    text = re.sub(r"\bh'-", "h-", text)
    text = re.sub(r"ä", "a", text)
    text = re.sub(r"ă", "a", text)
    text = re.sub(r"â", "à", text)
    text = re.sub(r"ā", "à", text)
    text = re.sub(r"ë", "e", text)
    text = re.sub(r"ĕ", "e", text)
    text = re.sub(r"ê", "è", text)
    text = re.sub(r"ē", "è", text)
    text = re.sub(r"ï", "i", text)
    text = re.sub(r"ĭ", "i", text)
    text = re.sub(r"î", "ì", text)
    text = re.sub(r"ī", "ì", text)
    text = re.sub(r"ŏ", "o", text)
    text = re.sub(r"ô", "ò", text)
    text = re.sub(r"ö", "ò", text)
    text = re.sub(r"ō", "ò", text)
    text = re.sub(r"ŭ", "u", text)
    text = re.sub(r"û", "ù", text)
    text = re.sub(r"ū", "ù", text)
    text = re.sub(r"\bDh' ", "Dh'", text)
    text = re.sub(r"\bdh-", "dh'", text)
    text = re.sub(r"\bDh-", "Dh-", text)
    #line = re.sub(teile, 'tèile', line)
    text = re.sub(r"coimh-", "co-", text)
    text = re.sub(r'choimh-', 'cho-', text)
    text = re.sub(r'roimh-', 'ro-', text)
    text = re.sub(r'comh-', 'co-', text)
    text = re.sub(r'chomh-', 'cho-', text)
    text = re.sub(r'-deug-', ' deug ', text)
    text = re.sub(r'-dheug-', ' dheug ', text)
    text = re.sub(r'-diag-', ' deug ', text)
    text = re.sub(r'-dhiag-', ' dheug ', text)

    text = re.sub(r'sàr-', 'sàr ', text)
    text = re.sub(r'shàr-', 'shàr ', text)

    text = re.sub(r"du-", "dubh ", text)
    text = re.sub(r"dhu-", "dhubh ", text)

    text = re.sub(r"\bt'", "d' ", text)
    text = re.sub(r"\bb'", "b' ", text)
    text = re.sub(r"\bB'", "B' ", text)
    text = re.sub(bad_comma, r"' ,\"", text)
    text = re.sub(all_hyphens, r'-', text)
    text = re.sub(double_space, r' ', text)
    
    '''
    Do caps version mate
    
    '''
    return text

