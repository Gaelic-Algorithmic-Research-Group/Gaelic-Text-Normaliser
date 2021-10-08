from sklearn_crfsuite import CRF
from sklearn_crfsuite import metrics
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline
from joblib import load

from .crf_model_aux import features

#predict takes and returns a list of sentences

def zip_tag_token(sentences, tag_sentences):
    tagged_sentences = []
    for sentence, tags in zip(sentences, tag_sentences):
        tagged_sentences.append(list(zip(sentence, tags)))
    return(tagged_sentences)

def pos_tag(sentences, model):
    tag_sentences = model.predict([[features(sentence, index) for index in range(len(sentence))] for sentence in sentences])
    return(zip_tag_token(sentences, tag_sentences))

'''
# load the model from disk
loaded_model = load('finalized_crf_model_gd.sav')

#x_test_sentences = getWordFromFeatures(x_test)

res = pos_tag(['Tha', 'mi', 'a\'', 'fuireach', 'ann', 'am', 'bùth', '!'], loaded_model)

print(res)

'''
