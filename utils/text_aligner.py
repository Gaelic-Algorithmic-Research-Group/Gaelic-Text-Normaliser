from Levenshtein import distance
from fuzzywuzzy import fuzz
from tqdm.auto import tqdm
import sys, os, numpy as np, matplotlib.pyplot as plt
sys.path.append('../')

from .utils import clean_token

def remove_newlines(text):
    nl = re.compile('\n')
    text = re.sub(nl, '', text)
    return ' '.join([i for i in text.split(' ') if i != ''])
    
def process_text(text, before=None):
    if before:
        return ' '.join(open(text,'r').read().splitlines()).split('.')
    else:
        return open(text,'r').read().split('.')

def align_tokens(text_before, text_after):
    aligned = []
    
    for idx in range(0, len(text_before)):
        before = text_before[idx]

        distances = []

        for i in text_after:

            distances.append((fuzz.ratio(before, i),i))
        aligned.append((before, max(distances)[1]))

    return aligned

def align_text(text_before, text_after):
    aligned = []
    
    for idx in tqdm(range(0, len(text_before)), total=len(text_before)):
        before = text_before[idx].strip()
        if len(before) < 5:
            continue
        distances = []
        for i in text_after:
            if len(i) < 5:
                continue
            distances.append((fuzz.ratio(before, i),i))
        aligned.append((before, max(distances)[1]))
        # try:
        #     for i in text_after[idx-10:idx+10]:
        #         if len(i) < 5:
        #             continue
        #         distances.append((fuzz.ratio(before, i),i))
        #     aligned.append((before, max(distances)[1]))

        # except:
        #     for i in text_after[idx-10:idx+10]:
        #         if len(i) < 5:
        #             continue
        #         distances.append((fuzz.ratio(before, i),i))
        #     aligned.append((before, max(distances)[1]))

    return aligned

def print_lines(aligned):

    for i in aligned:
        if len(i[0]) > 2:
            print('\nBefore\n')
            print(i[0])
            print('\nAfter\n')
            print(i[1])
            print()
            print('--'*30)
            print()

def list_match(list_a, list_b):
    max_len = max([len(list_a),len(list_b)])
    
    for i in tqdm([list_a, list_b]):

        while len(i) != max_len:
            i.append('')

    return list_a, list_b

def fetch_after(before_text, after_folder):
    ratios = []
    for i in os.listdir(after_folder):
        ratios.append((fuzz.ratio(before_text, i),i))

    return '{}{}'.format(after_folder, max(ratios)[1])

def align_texts(before_text, after_folder):

    print('Before text from: {}'.format(before_text))
    text_before = process_text(before_text, before=True)
    #after_text_file = fetch_after(before_text,after_folder)
    
    #print('After text file from: {}'.format(after_text_file))
    text_after = process_text(after_folder)
    text_before, text_after = list_match(text_before, text_after)
    aligned_text = align_text(text_before, text_after)
    aligned = AlignedDataset(aligned_text, clean_function=clean_token)
    return aligned


class AlignedDataset:
    
    def __init__(self, aligned_corpus, clean_function=None):
        
        self.clean_function = clean_function
        self.aligned_corpus = aligned_corpus
        self.before         = [i[0].strip() for i in aligned_corpus]
        self.after          = [i[1].strip() for i in aligned_corpus]
        self.distances = dict(enumerate(self.evaluate_alignment()))

    def print_evaluations(self):

        plt.plot(list(self.distances.values()))
        plt.ylabel('Ratio')
        plt.xlabel('Sentence Idx')
        plt.suptitle('Sentence Edit Ratio')
        plt.show()
    
    def evaluate_alignment(self):
    
        distances = []
        for b_line, a_line in self.aligned_corpus:
            distances.append(fuzz.ratio(b_line,a_line))

        return distances 

    def __getitem__(self, idx):
        
        return {'before' : self.before[idx],
                'after'  : self.after[idx],
                'idx'    : idx,
                'distance' : self.distances[idx]
               }
    
    def __len__(self):
        return len(self.aligned_corpus)
    
    def __str__(self):
        return "<Aligned Dataset>\n<{} lines>".format(len(self))
        
if __name__ == '__main__':
    before_text = '../data/gaelic/from_michael_before/_T_1949_12_A2__An_Gobha_\'s_an_Diabhol.txt'
    after_folder = '../data/gaelic/from_michael_before/'
    text_before = process_text(before_text, before=True)
    text_after = process_text(fetch_after(before_text,after_folder))
    text_before, text_after = list_match(text_before, text_after)
    aligned_text = align_text(text_before, text_after)
    aligned = AlignedDataset(aligned_text, clean_function=clean_token)
