from gd_analyser import tag, simple_tag, analyse, simple_analyse, tag_with_model, analyse_with_model
from joblib import load as job_load
from pickle import load as pick_load

with open('test_data/test.txt', encoding='utf-8-sig') as src, open('test_results/test-tagged.txt','w') as targ1, open('test_results/test-simple-tagged.txt','w') as targ2, open('test_results/test-analysed.txt','w') as targ3, open('test_results/test-simple-analysed.txt','w') as targ4, open('test_results/test-tagged-with-model.txt','w') as targ5, open('test_results/test-analysed-with-model.txt','w') as targ6:

    text = src.read()

    # tagger, model included in function (bad for multiple calls)
    tagged_sentences = tag(text)
    targ1.write('\n'.join(tagged_sentences))

    # simple tagger, model included in function (bad for multiple calls)
    simple_tagged_sentences = simple_tag(text)
    targ2.write('\n'.join(simple_tagged_sentences))

    # analyser, model and lexicon included in function (bad for multiple calls)
    analised_sentences = analyse(text)
    targ3.write('\n'.join(analised_sentences))

    # simple analyser, model and lexicon included in function (bad for multiple calls)
    simple_analised_sentences = simple_analyse(text)
    targ4.write('\n'.join(simple_analised_sentences))

    # Functions with external data loading (faster if you repeate tagging or analysis, because you load them once)
    tag_model = job_load('static/gd_model.sav')
    simple_tag_model = job_load('static/gd_simple_model.sav')
    ld_src = open('static/gd_dict.sav','rb')
    lexicon = pick_load(ld_src)
    ld_src.close()

    # tagger, model (simple or not) as parameter
    tagged_sentences_with_model = tag_with_model(text,tag_model)
    targ5.write('\n'.join(tagged_sentences_with_model))

    # analyser, model (simple or not) and lexicon as parameters
    analysed_sentences_with_model = analyse_with_model(text,tag_model,lexicon)
    targ6.write('\n'.join(analysed_sentences_with_model))



