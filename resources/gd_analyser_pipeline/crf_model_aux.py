

def isForeign(word):
    for letter in word:
        if letter in ['w', 'W', 'y', 'Y', 'k', 'K', 'x', 'X', 'z', 'Z', 'j', 'J', 'q', 'Q', 'v', 'V']:
            return(True)
    if 'oo' in word:
        return(True)
    if 'ee' in word:
        return(True)
    if 'pp' in word:
        return(True)
    if 'ss' in word:
        return(True)
    if 'ff' in word:
        return(True)
    if 'gg' in word:
        return(True)
    if 'cc' in word:
        return(True)
    return(False)

def features(sentence, index):
    """ sentence: [w1, w2, ...], index: the index of the word """
    return {
        'word': sentence[index],
        'wordlower': sentence[index].lower(),
        'is_first': index == 0,
        'is_last': index == len(sentence) - 1,
        'is_capitalized': sentence[index][0].upper() == sentence[index][0],
        'prefix-1': sentence[index][0],
        'prefix-2': sentence[index][:2],
        'prefix-3': sentence[index][:3],
        'suffix-1': sentence[index][-1],
        'suffix-2': sentence[index][-2:],
        'suffix-3': sentence[index][-3:],
        'prev_prev_word': '' if index == 0 or index == 1 else sentence[index - 2],
        'prev_word': '' if index == 0 else sentence[index - 1],
        'next_word': '' if index == len(sentence) - 1 else sentence[index + 1],
        'next_next_word': '' if index == len(sentence) - 1 or index == len(sentence) - 2 else sentence[index + 1],
        'has_hyphen': '-' in sentence[index],
        'is_numeric': sentence[index].isdigit(),
        'is_foreign': isForeign(sentence[index]),
        'capitals_inside': sentence[index][1:].lower() != sentence[index][1:]
    }
 

