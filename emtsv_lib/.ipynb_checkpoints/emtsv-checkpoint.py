#!/usr/bin/env python
# coding: utf-8

# In[1]:


# V 0.13
import dg2psg


# In[2]:


class Tags:
    fs = {}
    
    def __repr__(self):
        return 'emtsv.Tags'

    def __init__(self, text: str):
        self.fs = {}
        if text not in  ['_', '']:
            avs = text.split('|')
            for av in avs:
                [a, v] = av.split('=')
                self.fs[a] = v
    
            
    def __getitem__(self, attribute):
        if attribute in self.fs.keys():
            return self.fs[attribute]
        return ''
    
    def __str__(self):
        return self.to_str()
    
    def to_str(self):
        ret =  '|'.join([a+'='+v for a,v in self.fs.items()])
        return ret if ret != '' else '_'
    
    def items(self):
        return self.fs.items()
    
    def set(self, attribute, value):
        self.fs[attribute] = value


# In[3]:


class Word:
    header = ['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']
    v = {}
    
    def __repr__(self):
        return 'emtsv.Word'
    
    def __init__(self, 
               text: str, 
               header = -1):
        self.v = {}
        if header != -1:
            self.header = header
        values = text.split('\t')
        for label in self.header:
            i = self.header.index(label)
            if i < len(values):
                if values[i] == '':
                    self.v[label] = '_'
                else:
                    self.v[label] = values[i]
            else:
                self.v[label] = '_'
        
    def __getitem__(self, label):
        if label in self.v.keys():
            return self.v[label]
        return '_'
    
    def to_str(self, cols=[]):
        if cols == []:
            cols = self.header
        out = []
        for c in cols:
            if c in self.header:
                if type(self.v[c]).__name__ == 'Tags':
                    out += [self.v[c].to_str()]
                    continue
                out += [self.v[c]]
        return '\t'.join(out)

    def new_col(self, label, header):
        self.header = header
        self.v[label] = '_'
    
    def del_col(self, label: str):
        if label in self.v.keys():
            del self.v[label] 
        if label in self.header:
            self.header.remove(label)

    def set(self, attribute, value):
        if attribute != 'feats':
            self.v[attribute] = value
        else:
            self.v[attribute] = Tags(value) # újradefiniálja az összes feature-t
    
    def to_Tag(self, label):
        if label in self.header and type(self.v[label]).__name__ == 'str':
            self.v[label] = Tags(self.v[label])
        


# In[4]:


class Sentence:
    w = []
    len = 0
    deps = []
    allXPs = []
    CPs = []
    header=['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']
    
    def __repr__(self):
        return 'emtsv.Sentence'
    
    def __init__(self, 
               text: str = '', 
               header=['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']):
        
        self.w = []
        self.deps = []
        self.allXPs = []
        self.CPs = []
        self.header = header

        if text != '':
            words = text.split('\n')
            words = [w for w in words if len(w) > 2] # az üres sorokat kidobjuk
            for w in words:
                self.w.append(Word(w, header=header))
        
        self.len = len(self.w)
        
        if 'head' in self.header:
            self.deps = [int(w['head']) for w in self.w]
            self.allXPs = dg2psg.allMaxXP_recursive(1, self.len, self.deps)
            self.CPs = dg2psg.allSpecXP(self, 1, self.len, self.deps, self.CP_test)

    def __getitem__(self, i):
        return self.w[i]

    def add_word(self, w, after=''):
        if after == '':
            after = self.len
        
        if isinstance(w, str):
            w = Word(w, header=self.header)

        if isinstance(w, Word) and w.header == self.header:
            self.w.insert(after, w)
            self.len = len(self.w)
    
            if 'head' in self.header:
                self.deps = [int(w['head']) for w in self.w]
                self.allXPs = dg2psg.allMaxXP_recursive(1, self.len, self.deps)
                self.CPs = dg2psg.allSpecXP(self, 1, self.len, self.deps, self.CP_test)

            return w
        
        return None
    
    def to_text(self, start=1, to=''):
        if to == '':
            to = self.len
        ret = ''
        if start > to:
            return ret
        for i in range(start-1,to-1):
            ret += self.w[i]['form'] + self.w[i]['wsafter'][1:-1]
        ret += self.w[to-1]['form']
        return ret
    
    def __str__(self):
        return self.to_text()
    
    def to_str(self, cols=[]):
        if cols == []:
            cols = self.header
        return '\n'.join([w.to_str(cols) for w in self.w])
            
    def CP_test(self, sentence, start, head, end, d):
        if sentence[head-1]['upostag'] == 'VERB':
            return True
        if (int(sentence[head-1]['head']) == dg2psg.ROOT) and (sentence[head-1]['upostag'] not in ['X', 'PUNCT']):
            return True
        return False

    def arg_type(self, s, h, e):
        head = self.w[h]
        if head['upostag'] in ['PUNCT', 'X']:
            return '_'
        case = head['feats']['Case']
        if case != '':
            return case
        if head['upostag'] == 'VERB':
            mood = head['feats']['Mood']
            if mood != '':
                return mood
            else:
                return head['feats']['VerbForm']
        return head['upostag']
    
    def in_CP(self, w):
        if type(w) == 'emtsv.Word':
            w_id = int(w['id'])
        else: 
            w_id = w
        cps = []
        for cp in self.CPs:
            if w_id >= cp[0] and w_id <= cp[2]:
                cps.append(cp)
        return sorted(cps, key=lambda x: x[2] - x[0])
    
    def new_col(self, label, header):
        self.header = header
        for w in self.w:
            w.new_col(label, header)
    
    def del_col(self, label: str):
        for w in self.w:
            w.del_col(label)
        if label in self.header:
            self.header.remove(label)

#    def arg_type(self, start, head, end):
#        pass
    
    def to_Tag(self, label):
        if label in self.header:
            for w in self.w:
                w.to_Tag(label)

    def set(self, attribute, values):
        if len(values) != self.len:
            raise ValueError('Az értékek száma ('+str(len(values))+') nem egyezik meg a mondat szavainak számával ('+str(self.len)+')!')
        for i in range(self.len):
            self.w[i].set(attribute, values[i])

    def get(self, attribute):
        return [self.w[i][attribute] for i in range(self.len)]
    


# In[11]:


class Emtsv:
    '''
    emtsv-kódolt szöveg reprezentációja
    változók:
        header: az emtsv oszlopainak a címkéinek a listája
            az emtsv file első sorából zármazik
        default_header  = ['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']
        sentences: a szöveg mondatainak a listája, Sentence típusú értékek
    
    függvények:
        __init__    egy fájl szöveges tartalma alapján létrehozza a reprezentációt
        __getitem__ az i-dik mondatot adja vissza
        to_str      tsv formájú szöveggé alakítja vissza a reprezentációt
        to_tsv      tsv-fájlba menti a reprezentációt
        new_col     egy megadott címkéjű új oszlopot illeszt a reprezentációba 
                    minden szónál "_" értékkel
    '''
    
    default_header = ['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']
    header = []
    sentences = []
    len = 0
    
    def __repr__(self):
        return 'emtsv'
    
    def __str__(self):
        return self.to_str()
    
    def __init__(self, 
                 text: str = '',
                 header: str|list[str] = 'from_file'):
        '''
        '''
        
        self.sentences = []
        self.header = header

        if text != '':
        
            s0 = text.split('\n\n')
            
            if header == 'from_file':
                [header, s0[0]] = s0[0].split('\n', 1)
                self.header = header.split('\t')
            elif header == 'default':
                self.header = self.default_header
            
            for s in s0:
                if len(s) < 3: # ha véletlenül plusz üres sorok kerülnek a mondatok közé
                    continue
                self.sentences.append(Sentence(s, header=self.header))

            self.len = len(self.sentences)
        
    def __getitem__(self, i: int) -> Sentence:
        '''
        az i-dik mondatot adja vissza
        '''
        
        return self.sentences[i]

    def add_sentence(self, s='', after=''):
        if after == '':
            after = self.len

        if s == '':
            s = Sentence('', header=self.header)
        
        if isinstance(s, Sentence) and s.header == self.header:
            self.sentences.insert(after, s)
            self.len = len(self.sentences)

            return s
    
    def to_str(self, first=0, last=0, cols=[]) -> str:
        '''
        tab-szeparált szöveggé alakítja vissza a teljes reprezentációt
        '''
        if last == 0:
            last = self.len
        
        if cols == []:
            cols = self.header
        
        ret = '\t'.join([label for label in cols if label in self.header]) + '\n'
        ret += '\n\n'.join([s.to_str(cols=cols) for s in self.sentences[first:last]])
        return ret
    
    def to_tsv(self, file_name: str):
        '''
        tab-szeparált szövegként elmenti a file_name nevű fájlba a reprezentációt
        '''
        
        data = self.to_str()
        with open(file_name, 'w', encoding='utf8') as file:
            file.write(data)
    
    def new_col(self, label: str, position: int = -1):
        '''
        Új oszlopot illeszt a reprezentáció minden mondatának
        minden szavához üres "_" értékkel. Az oszlopot az i-dik 
        pozícióba szúrja be, default értékként az utolsó helyre.
        '''
        
        if position == -1:
            position = len(self.header)
            
        self.header.insert(position, label)
        
        for s in self.sentences:
            s.new_col(label, self.header)
    
    def del_col(self, label: str):
        for s in self.sentences:
            s.del_col(label)
        if label in self.header:
            self.header.remove(label)

    def to_Tag(self, label):
        if label in self.header:
            for s in self.sentences:
                s.to_Tag(label)
    
    def set_UID(self, label, prefix='', s_sep='s', w_sep='w', position=0):
        self.new_col(label, position)
        for s in range(len(self.sentences)):
            for w in range(len(self[s].w)):
                self.sentences[s][w].set(label, prefix + s_sep + str(s+1) + w_sep + str(w+1))

    def set(self, attribute, values):
        if len(values) != self.len:
            raise ValueError('Az értékek száma ('+str(len(values))+') nem egyezik meg a mondatok számával ('+str(self.len)+')!')
        for i in range(self.len):
            if len(values[i]) != self.sentences[i].len:
                raise ValueError('Az '+str(i+1)+ '. mondatban az értékek száma ('+str(len(values[i]))+') nem egyezik meg a mondat szavainak számával ('+str(self.sentences[i].len)+')!')
        for i in range(self.len):
            self.sentences[i].set(attribute, values[i])

    def get(self, attribute):
        return [self.sentences[i].get(attribute) for i in range(self.len)]


# In[6]:


def load_emtsv(file_name: str) -> Emtsv:
    '''
    a file_name nevű emtsv-kódolt fájlt olvassa be
    '''
    
    with open(file_name, 'r', encoding='utf8') as emtsv_file:
        data = emtsv_file.read()
    return Emtsv(data)
    


# In[7]:


def load_WA(WA_fname, header=''):
    '''
    A WA_fname nevű webAnno fájlban levő adatokat olvassa be
    Az első három oszlop neve 'id', 'chid', 'form' lesz, a többi oszlop nevét 
    a header argumentum adja meg (list of strings).
    Ha a header argumentum nincs specifikálva (''), akkor a webAnno fájl 
    első sorából veszi a többi oszlop nevét.
    '''
    base_header = ['id', 'chid', 'form']
    with open (WA_fname, 'r', encoding='utf8') as f:
        WA0 = f.readlines()
    if header == '':
        header = WA0[1].strip().split('|')[1:]
    header = base_header + header
    WA1 = []
    for line in WA0:
        if not line.startswith('#'):
            WA1.append(line)
    e = Emtsv(''.join(WA1), header)
    for s in e:
        for w in s:
            for c in WA_header:
                if w[c] == '*':
                    w.set(c,'_')
    return e


# In[8]:


def CP_type(sent:Sentence, h):
    she = [she for she in sent.CPs if she[1] == h]
    if she:
        (s,_,e) = she[0]
    else:
        return False

    head = sent[h-1]
    if head['head'] == dg2psg.ROOT:
        return 'main'

    sup = sent[int(sent[h-1]['head']) - 1]
    if sup['lemma'] == 'hogy':
        return 'CPhkm'

    XPs = dg2psg.allMaxXP2(s, h, e, sent.deps)
    for xp in XPs:
        if sent[xp[1]-1]['feats']['PronType'] == 'Rel':
            return 'CPrel'
    
    if head['feats']['VerbForm'] == 'Inf':
        return 'inf'
    
    if sup['upostag'] in ['SCONJ', 'CONJ']:
        return 'coord'
    
    return 'XXX'

