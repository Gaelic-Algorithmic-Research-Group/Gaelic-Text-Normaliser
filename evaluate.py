from GaelicTextNormaliser import TextNormaliser
from utils.utils import fetch_text
from utils.preprocess import preprocess_doc
import difflib, re
from tqdm.auto import tqdm as tt

all_apostrophes = re.compile(r"[’'`’‘]")

def count_Er_toks(gold_toks, bef_toks, norm_toks):

    errors = {'correctBefore' : 0,
              'correctAfter'  : 0,
              'incorrectBefore' : 0,
              'incorrectAfter' : 0}

    for i in gold_toks:

        if i not in bef_toks:
            errors['incorrectBefore']+=1

        if i in bef_toks:
            errors['correctBefore']+=1

        if i in norm_toks:
            errors['correctAfter']+=1
    for i in norm_toks:
        
        if i not in gold_toks and i not in bef_toks:
            errors['incorrectAfter'] += 1

    return errors

def calc_ER(errors):
    
    try:
        return (errors['correctAfter']-errors['correctBefore'])/errors['incorrectBefore']
    except ZeroDivisionError:
        return 0
    
def ER_of_line(b_line, g_line, n_line):
    
    g_toks=g_line.split(' ')
    b_toks=b_line.split(' ')
    n_toks=n_line.split(' ')
    errors=count_Er_toks(g_toks,b_toks,n_toks)
    return calc_ER(errors)

def count_tokens(tokens):
    counts = {}
    for token in tokens:
        if token not in counts:
            counts[token] = 1
        else:
            counts[token] += 1
    return counts

def calc_accuracy(t_line, g_line):
    
    t_toks=t_line.split(' ')
    g_toks=g_line.split(' ')
    t_counts = count_tokens(t_toks)
    g_counts = count_tokens(g_toks)
    
    not_in = 0
    
    for tok in t_toks:
        if tok in g_counts:
            t_counts[tok] -= 1
        else:
            not_in += 1
            
    return 1 - (sum(t_counts.values()) / sum(g_counts.values()))

def evaluate_text(before, gold, normalised):

    b_accuracy = []
    a_accuracy = []
    ers = []

    for b_line, g_line, n_line in zip(before, gold, normalised):

        bef_accuracy = calc_accuracy(b_line, g_line)
        b_accuracy.append(bef_accuracy)

        af_accuracy = calc_accuracy(n_line, g_line)
        a_accuracy.append(af_accuracy)

        er = ER_of_line(b_line, g_line, n_line)
        if er >= 0:
            ers.append(er)
        else:
            ers.append(0)
        #print(f'Bef: {bef_accuracy}\nAf: {af_accuracy}\nEr: {er}\n')

    avg_bef = sum(b_accuracy)/len(b_accuracy)
    avg_af = sum(a_accuracy)/ len(a_accuracy)
    avg_ers = sum(ers)/len(ers)
    print(f'Avg Bef: {avg_bef}\nAvg Af: {avg_af}\nAvg ER: {avg_ers}')
    return b_accuracy, a_accuracy, ers

def calc_confusion(tp_common_words, fn_added_words, fp_removed_words, tok=None, verbose=None):
    
    precision_ppv = len(tp_common_words) / (len(tp_common_words)+len(fp_removed_words))
    recall_TPR = len(tp_common_words) / (len(tp_common_words)+len(fn_added_words))
    try:
        f1_score = 2 * ((precision_ppv * recall_TPR)/ (precision_ppv+recall_TPR))
    except:
        f1_score = 0
    if verbose:
        print(f'Precision: {precision_ppv}')
        print(f'Recall: {recall_TPR}')
        print(f'F1 Score: {f1_score}')
    
    return precision_ppv, recall_TPR, f1_score
    
def gather_errors(doc_a, doc_b, tok=None):
    
    doc_a_toks = doc_a.split(' ')
    doc_b_toks = doc_b.split(' ')
    
    differences = difflib.ndiff(doc_a_toks, doc_b_toks)

    tp_common_words = []
    fn_added_words = []
    fp_removed_words = []
    
    num=None
    for i in differences:

        temp = [i for i in i.split(' ') if i not in ['', '?', '^\n', '^^^\n']]
        
        if tok:
            try:
                if temp[1] == tok:
                    num=True
                    #print(' '.join([i for i in differences]))
            except:
                None
                
        if len(temp) < 1:
            continue
        if temp[0] == '+':
            
            try:
                fn_added_words.append(temp[1])
            except:
                continue
                print(temp)

        elif temp[0] == '-':
            try:
                fp_removed_words.append(temp[1])
            except:
                continue
        else:
            tp_common_words.append(temp[0])
        
    
    return tp_common_words, fn_added_words, fp_removed_words, num

def update_wordlist(wordlist, fn, fp, line_idx):
        
    for words in fn:

        if words not in wordlist:
            wordlist[words] = {'count' : 1,
                               'idxs'  : [line_idx]}


        else:
            wordlist[words]['count']+=1
            wordlist[words]['idxs'].append(line_idx)
            
    for words in fp:
        
        if words not in wordlist:
            wordlist[words] = {'count' : 1,
                               'idxs'  : [line_idx]}

            
        else:
            wordlist[words]['count']+=1
            wordlist[words]['idxs'].append(line_idx)
    return wordlist

def calc_metrics(input_text, gold_text, norm_text, bad_words,idx=None, verbose=None, tok=None):
    
    metrics = {}
    
    bef_tp_common_words, bef_fn_added_words, bef_fp_removed_words, return_line = gather_errors(input_text, gold_text, tok=tok)
    norm_tp_common_words, norm_fn_added_words, norm_fp_removed_words, _ = gather_errors(norm_text, gold_text, tok=None)
    
    incorrect_before_normalisation = len(bef_fp_removed_words)
    correct_before_normalisation = len(bef_tp_common_words)
    
    correct_after_normalisation  = len(norm_tp_common_words)
    incorrect_after_normalisation = len(norm_fp_removed_words)
    
    bef_accuracy = len(bef_tp_common_words) / len(gold_text.split(' '))
    norm_accuracy  = len(norm_tp_common_words) / len(gold_text.split(' '))
    
    #error_reduction = (correct_after_normalisation-correct_before_normalisation)/incorrect_before_normalisation
    
    cb = (len(bef_tp_common_words)/len(gold_text.split(' ')))
    ib = (len(bef_fp_removed_words)+len(bef_fn_added_words)/len(gold_text.split(' ')))
    ca = (correct_after_normalisation/len(gold_text.split(' ')))
    
    bad_words = update_wordlist(bad_words, norm_fn_added_words, norm_fp_removed_words, idx)
    
    # before normalisation
    bef_precision_ppv, bef_recall_TPR, bef_f1_score =calc_confusion(bef_tp_common_words, bef_fn_added_words, bef_fp_removed_words)
    # normalised confusion
    norm_precision_ppv, norm_recall_TPR, norm_f1_score =calc_confusion(norm_tp_common_words, norm_fn_added_words, norm_fp_removed_words)
    
    try:
        er = ((ca-cb)/ib)
    except ZeroDivisionError:
        er = 1
        
    #print(f'Error 2: {er}\n')
    
    if er < 0:
        er = 0
    
    if verbose:
        print(f'{len(norm_tp_common_words)} True Positives')
        print(f'{len(norm_fn_added_words)} False Negatives')
        print(f'{len(norm_fp_removed_words)} False Positives\n')

        print(f'\nError Reduction: {er}')
        print(f'Accuracy Before Normalisation: {bef_accuracy}')
        print(f'Accuracy After Normalisation: {norm_accuracy}')
    
    metrics['bef_accuracy']=bef_accuracy
    metrics['af_accuracy']=norm_accuracy
    metrics['bef_precision']=bef_precision_ppv
    metrics['bef_recall']=bef_recall_TPR
    metrics['bef_f1']=bef_f1_score
    metrics['norm_precision']=norm_precision_ppv
    metrics['norm_recall']=norm_recall_TPR
    metrics['norm_f1']=norm_f1_score
    
    return metrics, bad_words, return_line

def update_metrics(upto, metrics, updated):

    for i in updated:
        metrics[i]+=(updated[i]/upto)
    return metrics

def gather_metrics(normaliser, target_text, gold_text):
    num=0
    
    bad_words={}
    
    total_bef_accuracy=[]
    total_af_accuracy = []
    total_er=[]
    precision=[]
    recall=[]
    total_f1_score=[]

    return_line = None
    error_lines=[]
    
    for bef, af in tt(zip(target_text, gold_text)):

        bef = re.sub(all_apostrophes, "'", bef)
        af = re.sub(all_apostrophes, "'", af)

        normalised_text = normaliser.normalise_doc(doc=bef)
        
        normalised_text = re.sub(all_apostrophes, "'", normalised_text)
        updated_metrics, bad_words, return_line = calc_metrics(bef, af, normalised_text, bad_words,idx=num, tok="a'")

        if return_line==True:
            error_lines.append(num)
        if num==0:
            metrics={i:0 for i in updated_metrics}

        metrics=update_metrics(1, metrics, updated_metrics)
        if num == 1:
            break
        num+=1
    
    return metrics, bad_words, 

def print_metrics(metrics):
    
    for key, val in metrics.items():
        
        val = val
        print(f'{key}: {val}\n')
        
    if metrics['af_accuracy'] > metrics['bef_accuracy']:
        
        improvement = round((metrics['af_accuracy']-metrics['bef_accuracy'])*100,7)
        print('Improved accuracy of {}%'.format(improvement))

def fetch_text(path):

    with open(path) as file:
        doc = file.read()

    doc = re.sub('\n', ' ', doc)
    return doc

def evaluate(bef_path, af_path, normaliser):
    bef_doc = fetch_text(bef_path)
    af_doc = fetch_text(af_path)
    metrics, bad_words = gather_metrics(normaliser, [bef_doc], [af_doc])
    print_metrics(metrics)
    return metrics 
    
if __name__ == '__main__':

    norm=TextNormaliser(from_config='config.yaml')
    tad_before = fetch_text('resources/data/test_cases/pre_goc.txt')
    tad_after = fetch_text('resources/data/test_cases/goc.txt')
    #normalised = norm.normalise_doc(doc_path='resources/data/test_cases/pre_goc.txt').split('\n')

    #b_accuracy, a_accuracy, ers = evaluate_text(tad_before, tad_after, normalised)

    metrics, bad_words = gather_metrics([norm], [tad_before], [tad_after])
    
