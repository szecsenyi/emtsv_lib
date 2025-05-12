#!/usr/bin/env python
# coding: utf-8

# In[3]:


# V 0.2.1
from dg2psg import dg2psg
import copy


# In[4]:


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


# In[5]:


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
    
    def set_header(self, new_header):
        self.header = new_header

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

    def select(self, test):
        return test(self)

        


# In[13]:


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
               text: str, 
               header=['form', 'wsafter', 'anas', 'lemma', 'xpostag', 'NP-BIO', 'upostag', 'feats', 'id', 'deprel', 'head', 'prev', 'previd', 'prevpos']):
        
        self.w = []
        self.deps = []
        self.allXPs = []
        self.CPs = []
        self.header = header
        
        words = text.split('\n')
        words = [w for w in words if len(w) > 2] # az üres sorokat kidobjuk
        for w in words:
            self.w.append(Word(w, header=header))
        
        self.len = len(self.w)
        self.deps = [int(w['head']) for w in self.w]
        self.allXPs = dg2psg.allMaxXP_recursive(1, self.len, self.deps)
        self.CPs = dg2psg.allSpecXP(self, 1, self.len, self.deps, self.CP_test)

    def __getitem__(self, i):
        return self.w[i]
    
    
    def to_text(self, start=1, to=-1):
        if to == -1:
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
    
    def set_header(self, new_header):
        self.header = new_header
        for w in self.w:
            w.set_header(new_header)

    def del_col(self, label: str):
        for w in self.w:
            w.del_col(label)
        if label in self.header:
            self.header.remove(label)

    def arg_type(self, start, head, end):
        pass
    
    def to_Tag(self, label):
        if label in self.header:
            for w in self.w:
                w.to_Tag(label)

    def select(self, test):
        ret = []
        for w in range(self.len):
            if self.w[w].select(test):
                ret.append(w)
        return ret


# In[14]:


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
    wlen = 0
    
    def __repr__(self):
        return 'emtsv'
    
    def __str__(self):
        return self.to_str()
    
    def __init__(self, 
                 text: str,
                 header: str|list[str] = 'from_file'):
        '''
        '''
        
        self.sentences = []
        self.header = header
        
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
        self.wlen = 0
        for s in self.sentences:
            self.wlen += s.len
        
    def __getitem__(self, i: int) -> Sentence:
        '''
        az i-dik mondatot adja vissza
        '''
        
        return self.sentences[i]
    
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

    def set_header(self, new_header):
        if len(self.header) != len(new_header):
            raise Exception("The number of column labels does not match")
        self.header = new_header
        for s in self.sentences:
            s.set_header(new_header)
    
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

    def append(self, other):
        o2 = copy.deepcopy(other)
        newHeader = self.header + [c for c in o2.header if c not in self.header]
        for c in newHeader:
            if c not in self.header:
                self.new_col(c)
            if c not in o2.header:
                o2.new_col(c)
        self.set_header(newHeader)
        o2.set_header(newHeader)
        self.sentences = self.sentences + o2.sentences
        self.len = len(self.sentences)
        self.wlen += o2.wlen
        del o2
        return self

    def select(self, test):
        ret = []
        for s in range(self.len):
            p = self.sentences[s].select(test)
            if p:
                ret.append((s, p))
        return ret


# In[15]:


def load_emtsv(file_name: str) -> Emtsv:
    '''
    a file_name nevű emtsv-kódolt fájlt olvassa be
    '''
    
    with open(file_name, 'r', encoding='utf8') as emtsv_file:
        data = emtsv_file.read()
    return Emtsv(data)
    


