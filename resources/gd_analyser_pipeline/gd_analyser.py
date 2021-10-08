from .seg import get_segmented_content_plain
from .crf_apply_model import pos_tag
from .gd_lex_lemma import lemmatise_text
from joblib import load as job_load
from pickle import load as pick_load

def is_newline(sentence):
    return(len(sentence) == 1 and sentence[0][0] == '\n')

def is_metaline(sentence):
    return(len(sentence) == 1 and sentence[0][0][0] == '#')

# 2 args : token + tags
def make_pretty_2(tagged_sentence):
    if is_newline(tagged_sentence):
        return('# newline')
    if is_metaline(tagged_sentence):
        return(tagged_sentence[0][0])
    pretty_sentence = []
    for word, tag in tagged_sentence:
        pretty_sentence.append('\t'.join([word, tag])) 
    pretty_sentence.append('') 
    return('\n'.join(pretty_sentence))

# 3 args : token + lemma + tags
def make_pretty_3(tagged_sentence):
    if is_newline(tagged_sentence):
        return('# newline')
    if is_metaline(tagged_sentence):
        return(tagged_sentence[0][0])
    pretty_sentence = []
    for word, lemma, tag in tagged_sentence:
        pretty_sentence.append('\t'.join([word, lemma, tag])) 
    pretty_sentence.append('') 
    return('\n'.join(pretty_sentence))

def tag(rough_text):
    loaded_model = job_load('static/gd_model.sav')

    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, loaded_model)
    return [make_pretty_2(tagged_sentence) for tagged_sentence in tagged_sentences]

def simple_tag(rough_text, model_path=None, loaded_model=None):

    if not loaded_model:
        default_model_path = 'static/gd_simple_model.sav'
        if not model_path:
            model_path = default_model_path

        loaded_model = job_load(model_path)

    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, loaded_model)
    return [make_pretty_2(tagged_sentence) for tagged_sentence in tagged_sentences]

def tag_with_model(rough_text,model):
    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, model)
    return [make_pretty_2(tagged_sentence) for tagged_sentence in tagged_sentences]

def analyse(rough_text, model_path=None, src=None):
    

    default_model_path = 'static/gd_simple_model.sav'
    default_src = 'static/gd_dict.sav'

    if not model_path:
        model_path = default_model_path
    if not src:
        src = default_src

    loaded_model = job_load(model_path)
    ld_src = open(src,'rb')
    loaded_lexicon = pick_load(ld_src)
    ld_src.close()

    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, loaded_model)
    lem_tagged_sentences = lemmatise_text(tagged_sentences,loaded_lexicon)
    return [make_pretty_3(lem_tagged_sentence) for lem_tagged_sentence in lem_tagged_sentences]

def simple_analyse(rough_text, model_path=None, src=None):
    default_model_path = 'static/gd_simple_model.sav'
    default_src = 'static/gd_dict.sav'
    if not model_path:
        model_path = default_model_path
    if not src:
        src = default_src

    loaded_model = job_load(model_path)
    ld_src = open(src,'rb')
    loaded_lexicon = pick_load(ld_src)
    ld_src.close()

    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, loaded_model)
    lem_tagged_sentences = lemmatise_text(tagged_sentences,loaded_lexicon)
    return [make_pretty_3(lem_tagged_sentence) for lem_tagged_sentence in lem_tagged_sentences]

def analyse_with_model(rough_text,tag_model,lexicon):
    segmented_sentences = get_segmented_content_plain(rough_text)
    tagged_sentences = pos_tag(segmented_sentences, tag_model)
    lem_tagged_sentences = lemmatise_text(tagged_sentences,lexicon)
    return [make_pretty_3(lem_tagged_sentence) for lem_tagged_sentence in lem_tagged_sentences]


