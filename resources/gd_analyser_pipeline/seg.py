# FILE STANDARTISATION

def std_text(text):
    return(text.replace('\r\n','\n').replace('\r','\n')) 


def before_newline(string):
    if len(string) < 2:
        return(False)
    return(string[1] == '\n')

def rmv_newline_seq(text):
    text2 = []
    for i in range(len(text)):
        if not (text[i] == '\n' and before_newline(text[i:])):
            text2.append(text[i])
    return(text2)


# WORD SEGMENTATION

separables = ['.',',',' ','?','!','$','%','€','£','+','•',')',':',';','(','\n','\t','\r','\"','“','”','–','…',']','[','>','<','*']


def w_segment0(string):
    string2 = []
    for c in string:
        if c in separables:
           string2.extend(['^',c,'^'])
        else:
           string2.append(c)
    return(''.join(string2))


def w_segment0x(string):
    string2 = []
    status = 'x'
    # ('x' neutral, 'l' eol, 'm' meta)
    for c in string:
        if status == 'm':
            if c == '\n':
               string2.extend(['~',c])
               status = 'l'
            else:
               string2.append(c)
        elif status == 'l':
            if c == '#':
               string2.extend(['~','#'])
               status = 'm'
            elif c == '\n':
               string2.extend(['^',c,'^'])
               status = 'l'
            else:
                if c in separables:
                    string2.extend(['^',c,'^'])
                else:
                    string2.append(c)
                status = 'x'
        else:
            if c == '\n':
               string2.extend(['^',c,'^'])
               status = 'l'
            else:
                if c in separables:
                    string2.extend(['^',c,'^'])
                else:
                    string2.append(c)
                status = 'x'
    return(''.join(string2))

#rmv double ^^

def w_segment1(string):
    string2 = []
    i = 0
    while i < len(string):
        if string[i:i+2] == '^^':
            i = i + 1
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))

#rmv merge sequencial stars and dots

def w_segment1b(string):
    string2 = []
    i = 0
    while i < len(string):
        if string[i:i+3] == '.^.' or string[i:i+3] == '*^*':
            string2.append(string[i])
            i = i + 2
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))


def w_segment2(string):
    string2 = []
    i = 0
    while i < len(string):
        if string[i:i+6] == '^!^..^':
            string2.append('^!..')
            i = i + 4
        elif string[i:i+6] == '^?^..^':
            string2.append('^?..')
            i = i + 4
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))


def w_segment(text):
    return(w_segment2(w_segment1b(w_segment1(w_segment0(text)))))

def w_segmentx(text):
    return(w_segment2(w_segment1b(w_segment1(w_segment0(text)))))


# Reglue numerical expressions with dot or comma

def w_reglue0(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+5]
        if string_to_scan[0].isdigit() and (string_to_scan[1:4] == '^,^' or string_to_scan[1:4] == '^.^') and string_to_scan[4].isdigit():
            string2.append(string[i])
            string2.append(string_to_scan[2])
            i = i + 4
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))

# Reglue weblink and similar

def w_reglue1(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+5]
        if len(string_to_scan) < 5:
            string2.append(string[i])
            i = i + 1
        elif not string_to_scan[0] in separables and string_to_scan[1:4] == '^.^' and not string_to_scan[4] in separables:
            string2.append(string[i])
            string2.append('.')
            i = i + 4
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))


#reglue xml tags


def before_letter_or_slash(string):
    if len(string) < 3:
        return(False)
    return(string[2].isalpha() or string[2] == '/') 
    #string[i] is '^'

def w_reglue2(string):
    string2 = []
    i = 0
    in_tag = False
    while i < len(string):
        if not in_tag:
            if string[i] == '<' and before_letter_or_slash(string[i:]):
                in_tag = True
            string2.append(string[i])
        else:
            if string[i] == '>':
                in_tag = False
            if string[i] != '^':
                string2.append(string[i])
        i = i + 1
    return(''.join(string2))


def tokenise(text):
    return(w_reglue2(w_reglue1(w_reglue0(w_segment2(w_segment1b(w_segment1(w_segment0x(text))))))))


# SENTENCE SEGMENTATION

right_breakables = ['.','?','!',':',';','…']
left_breakables = ['\n','\r']


def is_metaline(string):
    string_to_scan = string[0:2]
    if len(string_to_scan) < 2:
        return(False)
    return(string_to_scan[0:2] == '~#')

def s_segment0(string):
    string2 = []
    i = 0
    unparsed = False
    while i < len(string):
        if unparsed:
            if string[i] == '\n':
                unparsed = False
            else:
                string2.append(string[i])
                i = i + 1
        else:
            if is_metaline(string[i:]):
                unparsed = True
            else:
                string_to_scan = string[i:i+2]
                if len(string_to_scan) < 2:
                    string2.append(string[i])
                    i = i + 1
                elif string_to_scan[0] == '^' and string_to_scan[1] in left_breakables:
                    string2.append('|')
                    string2.append(string_to_scan[1])
                    string2.append('|')
                    i = i + 2
                elif string_to_scan[1] == '^' and string_to_scan[0] in right_breakables:
                    string2.append(string_to_scan[0])
                    string2.append('|')
                    i = i + 2
                else:
                    string2.append(string[i])
                    i = i + 1
    return(''.join(string2))

def s_correct1(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+3]
        if len(string_to_scan) < 3:
            string2.append(string[i])
            i = i + 1
        elif string_to_scan == '.|\"' or string_to_scan == '.|”' or string_to_scan == '.|)':
            string2.append(string_to_scan[0])
            string2.append('^')
            string2.append(string_to_scan[2])
            string2.append('|')
            i = i + 3
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))

# false sentence end (before lower)

def s_reglue1b(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+5]
        if len(string_to_scan) < 5:
            string2.append(string[i])
            i = i + 1
        elif string_to_scan == '.| ^' and string_to_scan[4].islower():
            string2.append('.^ ^')
            i = i + 4
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))

# false sentence end (first name initial)

def s_reglue1c(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+5]
        if len(string_to_scan) < 5:
            string2.append(string[i])
            i = i + 1
        elif string_to_scan[0] == '^' and string_to_scan[1].isupper() and string_to_scan[2:] == '^.|':
            string2.append(string_to_scan[0:4])
            i = i + 5
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))

# no sentence btw ! ir ? and so on

def s_reglue1d(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+3]
        if len(string_to_scan) < 3:
            string2.append(string[i])
            i = i + 1
        elif string_to_scan in ['?|?','?|.','?|!','?|…','!|!','!|?','!|.','!|…']:
            string2.append(string_to_scan[0])
            string2.append('^')
            i = i + 2
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))



def s_correct2(string):
    string2 = []
    i = 0
    while i < len(string):
        string_to_scan = string[i:i+2]
        if string_to_scan == '||':
            i = i + 1
        elif string_to_scan == '|^':
            string2.append(string[i])
            i = i + 2
        #simplify metaline start
        elif string_to_scan == '~#':
            string2.append('#')
            i = i + 2
        #simplify metaline end
        elif string_to_scan == '~\n':
            string2.append('|')
            string2.append('\n')
            i = i + 2
        elif string_to_scan == '\n^':
            string2.append(string[i])
            string2.append('|')
            i = i + 2
        else:
            string2.append(string[i])
            i = i + 1
    return(''.join(string2))



# GET SEGMENTED CONTENT

def get_segmented_content(text):
    segmented_text = segment(text)
    sentences = segmented_text.split('|')
    return([sentence.split('^') for sentence in sentences if sentence != ''])


def is_plain(token):
    return(not token in [' ','\t',''])


# without spaces and tabs
def get_segmented_content_plain(text):
    segmented_text = get_segmented_content(text)
    plain_segmented_text = [[w for w in sentence if is_plain(w)] for sentence in segmented_text]
    return(plain_segmented_text)
#    return([sentence for sentence in plain_segmented_text if sentence ])


def segment(text):
    return(s_correct2(s_reglue1d(s_reglue1c(s_reglue1b(s_correct1(s_segment0(tokenise(text))))))))


def mk_arcosg_w_seg(segmented_sentence):
    arcosg_segmented_sentence = []
    for token in segmented_sentence:
        if token.startswith('h-') or token.startswith('t-') or token.startswith('n-'):
            arcosg_segmented_sentence.append(token[0:2])
            arcosg_segmented_sentence.append(token[2:])
        else:
            arcosg_segmented_sentence.append(token)
    return(arcosg_segmented_sentence)

def mk_arcosg_seg(segmented_text):
     return[mk_arcosg_w_seg(sentence) for sentence in segmented_text]
