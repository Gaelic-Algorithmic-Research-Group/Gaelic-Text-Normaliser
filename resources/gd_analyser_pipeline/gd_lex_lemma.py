from .lemma_dict import find_tagged_string_in_dict

def lemmatise_pron(token, tag):
    prep_token = ''
    if token in ['agam', '\'gam', '’gam', 'agamsa', '\'gad', '’gad', 'agad', 'agadsa', 'aige', 'ga', 'aigesan', 'aice', 'aicese', 'againn', '\'gar', '’gar', 'againne', 'agaibh', '\'gur', '’gur', 'agaibhse', 'aca', 'gan', '’gan', 'acasan']:
        prep_token = 'aig + '
    if token in ['orm', 'ormsa', 'ort', 'ortsa', 'airsan', 'oirre', 'oirrese', 'oirnn', 'oirnne', 'oirbh', 'oirbhse', 'orra', 'orrasan']:
        prep_token = 'air + '
    if token in ['anns', 'annam', '\'nam', '’nam', 'annamsa', 'annad', '\'nad', '’nad', 'annadsa', '\'na', '’na', 'annsan', 'innte', 'inntese', 'annainn', '\'nar', '’nar', 'annainne', 'annaibh', '\'nur', '’nur', 'annaibhse', 'annta', '\'nan', '’nan', 'anntasan']:
        prep_token = 'ann + '
    if token in ['às', 'asam', 'asad', 'aisde', 'asainn', 'asaibh', 'asda']:
        prep_token = 'à + '
    if token in ['bhon', 'bhuam', 'bhom', 'bhuat', 'bhod', 'bhuaithe', 'bhuaipe', 'bhuainn', 'bhor', 'bhuaibh', 'bhu', 'bhuapa']:
        prep_token = 'bho + '
    if token in ['dhen', 'dhiom', 'dhem', 'dhiot', 'dhed', 'dheth', 'dhith', 'dhinn', 'dhibh', 'dhiubh']:
        prep_token = 'de + '
    if token in ['don', 'dhomh', 'dom', 'dham', 'dhomhsa', 'dhut', 'dod', 'dhad', 'dhutsa', 'dha', 'da', 'dhasan', 'dhi', 'dhise', 'dhuinn', 'dor', 'dhar', 'dhuinne', 'dhuibh', 'dhur', 'dhuibhse', 'dhaibh', 'dhaibhsan']:
        prep_token = 'do + '
    if token in ['fon', 'fodham', 'fom', 'fodhad', 'fod', 'fodha', 'foidhpe', 'fodhainn', 'for', 'fodhaibh', 'fur', 'fodhpa']:
        prep_token = 'fo + '
    if token in ['eadarainn', 'eadaraibh', 'eatorra']:
        prep_token = 'eadar + '
    if token in ['chun', 'thun', 'ugam', 'thugam', 'chugam', 'gum', 'ugad', 'thugad', 'chugad', 'gud', 'uige', 'thuige', 'chuige', 'uice', 'thuice', 'chuice', 'ugainn', 'thugainn', 'chugainn', 'gar', 'ugaibh', 'thugaibh', 'chugaibh', 'gur', 'uca', 'thuca', 'chuca', 'gun']:
        prep_token = 'gu + '
    if token in ['leam', 'leamsa', 'lem', 'leat', 'leatsa', 'led', 'leis', 'leisan', 'leatha', 'leathase', 'leinn', 'leinne', 'ler', 'leibh', 'leibhse', 'lur', 'leotha', 'leothasan', 'leò', 'len']:
        prep_token = 'le + '
    if token in ['mun', 'umam', '\'mum', '’mum', 'umad', '\'mud', '’mud', 'uime', 'uimpe', 'umainn', 'mar', 'umaibh', 'mur', 'umpa', 'man', 'mam']:
        prep_token = 'mu + '
    if token in ['on', 'uam', 'om', 'uat', 'od', 'uaithe', 'uaipe', 'uainn', 'or', 'uaibh', 'ur', 'uapa']:
        prep_token = 'o + '
    if token in ['rium', 'rim', 'ruit', 'rid', 'ris', 'rithe', 'ruinn', 'ruibh', 'riutha', 'rin']:
        prep_token = 'ri + '
    if token in ['ron', 'romham', 'rom', 'romhad', 'rod', 'roimh', 'roimhe', 'roimhpe', 'romhainn', 'ror', 'romhaibh', 'rur', 'romhpa']:
        prep_token = 'ro + '
    if token in ['tharam', 'tharad', 'thairis', 'thairte', 'tharainn', 'tharaibh', 'tharta']:
        prep_token = 'thar + '
    if token in ['tron', 'tromham', 'trom', 'tromhad', 'trod', 'troimhe', 'troimhpe', 'tromhainn', 'tror', 'tromhaibh', 'trur', 'tromhpa']:
        prep_token = 'tro + '
    if tag.startswith('3sm', 2):
        prep_token = prep_token + 'e'
    if tag.startswith('3sf', 2):
        prep_token = prep_token + 'i'
    if tag.startswith('3p', 2):
        prep_token = prep_token + 'iad'
    if tag.startswith('1s', 2):
        prep_token = prep_token + 'mi'
    if tag.startswith('2s', 2):
        prep_token = prep_token + 'thu'
    if tag.startswith('2p', 2):
        prep_token = prep_token + 'sibh'
    if tag.startswith('1p', 2):
        prep_token = prep_token + 'sinn'
    return(prep_token)



def lemmatise_token(tagged_token,loaded_dict):
    if len(tagged_token) != 2:
        return(tagged_token)
    if tagged_token[1][0] == 'P':
       lemma = lemmatise_pron(tagged_token[0],tagged_token[1])
       if lemma != '':
           return [tagged_token[0], lemma, tagged_token[1]]
    lemmas = find_tagged_string_in_dict(loaded_dict, tagged_token[0], tagged_token[1][0])
    if lemmas == None or lemmas == []:
        lower_lemmas = find_tagged_string_in_dict(loaded_dict, tagged_token[0].lower(), tagged_token[1][0])
        if lower_lemmas == None or lower_lemmas == []:
                return [tagged_token[0], tagged_token[0], tagged_token[1]]
        return [tagged_token[0], lower_lemmas[0], tagged_token[1]]
    return [tagged_token[0], lemmas[0], tagged_token[1]]

def lemmatise_sentence(tagged_sentence,loaded_dict):
    return [lemmatise_token(tagged_token,loaded_dict) for tagged_token in tagged_sentence]

def lemmatise_text(tagged_sentences,loaded_dict):
    return [lemmatise_sentence(tagged_sentence,loaded_dict) for tagged_sentence in tagged_sentences]
    


