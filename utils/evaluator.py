import re, subprocess as sub, argparse
import sys

false_neg = re.compile(r'{\+.+\+}')
false_pos = re.compile(r'\[-.+-\]')

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('before', help="Source Document")
    p.add_argument('gold', help="Manually Annotated Document")
    p.add_argument('norm', help="Normalised Docuement")
    p.add_argument('--verbose', help="Show evaluation per line")
    p.add_argument('--line_num', help="Print until line n", default=1)
    p = p.parse_args()

    return p

double_space = re.compile('  ')


def fix_formatting(line):
    line = re.sub(double_space, ' ', line)
    return line


def evaluate_normaliser(before_norm, after_norm, norm_text, max_len=None, verbose=None):

    idx = 0
    stats = {'AccuracyBefore': 0,
             'AccuracyAfter' : 0,
             'ErrorReduction': 0}
    
    lines_with_errors = 0
    for b, a, n in zip(before_norm, after_norm, norm_text):

        b = fix_formatting(b)
        a = fix_formatting(a)
        if max_len:

            if len(b.split(' ')) > max_len:
                idx += 1
                continue

        if verbose:
            print('\nLine: {}'.format(idx))

        ab, na, er = accuracy(b,a, norm=n, er=1)

        stats['AccuracyBefore'] += (ab/len(before_norm))
        stats['AccuracyAfter'] += (na/len(before_norm))

        if er == 0:
            stats['ErrorReduction'] += 0
        else:
            lines_with_errors += 1
            stats['ErrorReduction'] += er
        if verbose:

            print('''
    Before     : {}
    Gold       : {}
    Normalised : {}

    AccuracyBefore  : {}
    AccuracyAfter   : {}
    Error Reduction : {}'''.format(b,a, n, ab, na, er))

            idx += 1

    #     print((stats['ErrorReduction']/lines_with_errors)*100)
    #     print(lines_with_errors)
    stats['AccuracyBefore'] = round(stats['AccuracyBefore'], 4)* 100
    stats['AccuracyAfter'] = round(stats['AccuracyAfter'], 4)* 100
    
    try:
        stats['ErrorReduction'] = round(lines_with_errors/ stats['ErrorReduction'],2)
    except:
        stats['ErrorReduction'] = 'You Fudged Up!'
    return stats


def remove_punctuation(token):
    punct = re.compile(r"[',\.\"]")
    return re.sub(punct,'',token)


def fetch_text(path):
    
    return [i for i in open(path).read().splitlines() if i != '']


def norm_document(doc, output_path=None, return_backend=None):
    
    normalised_lines = []
    backend = []
    if output_path:
        
        with open(output_path, 'w') as file:

            for i in doc:
                normalised = norm.normalise_line(i)
                normalised_lines.append(normalised)
                file.write('{}\n'.format(normalised))
        
    else:
        
        for i in doc:
            
            if return_backend:
                
                normalised, end = norm.normalise_line(i, return_backend)
                backend.append(end)
                
            else:
                normalised = norm.normalise_line(i)
                
            normalised_lines.append(normalised)
                
    return normalised_lines, backend

def wdiff_doc(doc_a, doc_b):
    wdiff_doc = sub.Popen(['wdiff', '-s', doc_a, doc_b,], stdout=sub.PIPE)
    stats = wdiff_doc.communicate()
    return ' '.join(stats[0].decode('utf-8',errors='ignore').splitlines())

def accuracy(line, gold, norm=None, er=None, verbose=None):
    line_map = count_tokens(line)
    gold_map = count_tokens(gold)
    if verbose:
        print('\nBefore Word Count: {}'.format(sum(line_map.values())))
        print('Gold Word Count: {}'.format(sum(gold_map.values())))
    ba = norm_accuracy(line_map, gold_map)
    
    if norm:
        norm_map = count_tokens(norm)   
        na = norm_accuracy(norm_map, gold_map)
        if verbose:
            print('Norm Word Count: {}'.format(sum(norm_map.values())))
        if er:
            er= calc_error_reduction(line_map,gold_map,norm_map)
            return ba, na, er
        
        return ba, na

    return ba

def build_stats(wdiff_string, num_lines):
    
    matrix = {'TruPos' : 0,
              'FalPos' : 0,
              'FalNeg' : 0}
    
    for i in wdiff_string.split(' '):

        if re.match(false_neg, i):
            matrix['FalNeg'] += 1
    #         norm_map[i] = {'type' : 'insertion'}
    #         norm_token = i 

        elif re.match(false_pos, i):
            matrix['FalPos'] += 1

        else:
            matrix['TruPos'] += 1
    #         if i not in norm_map:
    #             norm_map[i] = {'type' : 'addition'}
    #         norm_map[norm_token]['replacement'] : i
        if num_lines:
            num_lines -= 1

            if num_lines == 0:
                break
    return matrix

def f_score(precision, recall):
    return 2* ((precision*recall) / (precision + recall))

def print_stats(matrix):
    precision = matrix['TruPos']/ (matrix['TruPos'] + matrix['FalPos'])
    recall = matrix['TruPos'] / (matrix['FalNeg'] + matrix['TruPos'])
    fscore = f_score(precision, recall)
    
    return'''
    Precision : {}
    Recall    : {}
    F1_Score  : {}
    '''.format(precision, recall, fscore)

def count_tokens(line):
    
    token_counter = {}
    
    tokenised = remove_punctuation(line).split(' ')
    
    for i in tokenised:
        if i not in token_counter:
            token_counter[i] =1
        else:
            token_counter[i] +=1
    
    return token_counter

def norm_accuracy(norm, gold):
    
    na = 0
    
    for i in norm:
        if i in gold:
            na += 1
    
    return na / sum(gold.values())

def calc_error_reduction(before_counts, gold_counts, norm_counts):
    correct_before_norm = count_correct(before_counts, gold_counts)
    correct_after_norm = count_correct(norm_counts, gold_counts)
    incorrect_before_norm = count_correct(before_counts,gold_counts, ic_before=True)
    
    if incorrect_before_norm == 0:
        return 0
    
    return (correct_after_norm - correct_before_norm) / incorrect_before_norm

def count_correct(bef, gold, ic_before=None):
    
    ib = 0
    cb = 0
    
    for i in bef:
        if i in gold:
            cb += 1
        else:
            ib += 1
            
    if ic_before:
        
        if ib == 0:
            return 0
        return ib / sum(gold.values())
    
    return cb / sum(gold.values())

class Evaluator:
    
    def __init__(self, before_path, gold_path, norm_path, verbose=None, num_lines=None):
        
        self.before_path = before_path
        self.gold_path = gold_path
        self.norm_path = norm_path
        self.verbose = verbose
        self.num_lines = num_lines

    def confusion_matrix(self):
        
        self.b42gold_wdiff   = wdiff_doc(self.before_path, self.gold_path)
        self.norm2gold_wdiff = wdiff_doc(self.norm_path, self.gold_path)
        self.before2gold_matrix = build_stats(self.b42gold_wdiff, self.num_lines)
        self.norm2gold_matrix   = build_stats(self.norm2gold_wdiff, self.num_lines)
        
    def show_stats(self, line_num):
        
        idx = 0
        for i, x in zip([self.before2gold_matrix, self.norm2gold_matrix], ['Source2Gold','Norm2Gold']):
            if idx == line_num:
                break
            print(i)
            print(x)
            print(print_stats(i))
            idx += 1

    def print_stats(self,verbose=None, max_len=None):
        print('Printing Stats')

        self.stats = evaluate_normaliser(fetch_text(self.before_path),
                                         fetch_text(self.gold_path),
                                         fetch_text(self.norm_path), verbose=verbose, max_len=max_len)

def evaluate(args):

    print('\nEvaluating Text with wdiff\n')
    evaluator = Evaluator(args.before, args.gold, args.norm)
    if args.verbose == 1:
        evaluator.confusion_matrix()
    elif args.verbose == 2:
        evaluator.show_stats()
    elif args.verbose ==3:
        evaluator.confusion_matrix()
        evaluator.show_stats(args.line_num)
        evaluator.print_stats(args.line_num)

    return evaluator

if __name__ == '__main__':
    args = get_args()
    evaluate(args)