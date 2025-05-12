class dg2psg:
    ROOT = 0
    NOHEAD = -1
    MULTIHEAD = -2

    @staticmethod
    def closedXP(start: int, end: int, d: list[int]) -> int:
        '''
        Ellenőrzi, hogy a d függőségi listában a start-tal kezdődő és end-del 
        végződő rész összefüggő-e, azaz pontosan egy elem < start vagy > end.
        A d lista nullánál nagyobb egészeket tartalmaz, ezért az első elemére 
        1-gyel hivatkozunk
        
        - start: kezdő index
        - end: végső index
        - d: a függőségi élek listája
        '''
        
        head = NOHEAD # no head
        
        for i in range(start-1,end):
            if d[i]<start or d[i]>end or d[i]==ROOT:
                if head == NOHEAD:
                    head = i+1
                else:
                    return MULTIHEAD
        
        return head

    @staticmethod
    def firstMaxXP(start: int, end: int, d: list[int], checkNohead = False) -> tuple[int, int, int]:
        '''
        a start…end tartományba eső első maxXP-t adja vissza 
        visszaadott érték: az első maxXP a tartományban: (XPstart, XPhead, XPend)
        
        - start: kezdő index; 
        - end: végső index; 
        - d: a függőségi élek listája 
        '''
        
        if start == end:
            return (start, end, end) # egyszavas frázis 
        
        head = closedXP(start,end,d)

        if head == NOHEAD and checkNohead:
            raise Exception('Dependency graph is cyclic', start, end)
        if head == MULTIHEAD or head == NOHEAD:
            return firstMaxXP(start,end-1,d, checkNohead)
        else:
            return (start, head, end)

    @staticmethod
    def allMaxXP(start: int, end: int, d: list[int], checkNohead = False) -> list[tuple[int, int, int]]:
        '''
        a start…end tartományba eső összes maxXP-t adja vissza
        visszaadott érték: az maxXP-k listája a tartományban: [(XPstart, XPhead, XPend), …]
        
        - start: kezdő index
        - end: végső index; 
        - d: a függőségi élek listája
        '''
        
        allXP = []
        
        if start == end:
            (start1, head1, end1) = (start, start, end)
        else:
            (start1, head1, end1) = firstMaxXP(start,end,d, checkNohead)
        
        allXP = [(start1, head1, end1)]
        
        if end1 < end:
            restXP = allMaxXP(end1+1, end, d, checkNohead)
            allXP = allXP+restXP
        
        return allXP
    
    @staticmethod
    def allMaxXP2(start: int, head: int, end: int, d: list[int]) -> list[tuple[int, int, int]]:
        '''
        a start…head és a head…end tartományba eső összes maxXP-t adja vissza
        visszaadott érték: az maxXP-k listája a tartományban: [(XPstart, XPhead, XPend), …]
        
        - start: kezdő index
        - head: a fej indexe: az eze előtti és mögötti maxXP-ket keresi
        - end: végső index; 
        - d: a függőségi élek listája
        '''
        
        allXP = []
        
        if start < head:
            allXP += allMaxXP(start, head-1, d)
            
        if head < end:
            allXP += allMaxXP(head+1, end, d)
            
        return allXP
    
    @staticmethod
    def allMaxXP_recursive(start: int, end: int, d: list[int], checkNohead = False) -> list[tuple[int, int, int]]:
        '''
        a start…end tartományba eső összes maxXP-t adja vissza rekurzívan
        visszaadott érték: az összes maxXP listája a tartományban: [(XPstart, XPhead, XPend), …]
        
        - start: kezdő index
        - end: végső index
        - d: a függőségi élek listája
        '''
        
        allXP = []
        
        if start == end:
            (start1, head1, end1) = (start, start, end)
        else:
            (start1, head1, end1) = firstMaxXP(start,end,d,checkNohead)
            
        allXP = [(start1, head1, end1)]
        
        if start1 < head1:
            XPsBeforeHead = allMaxXP_recursive(start1, head1-1, d, checkNohead)
            allXP = allXP + XPsBeforeHead
            
        if head1 < end1:
            XPsAfterHead = allMaxXP_recursive(head1+1, end1, d, checkNohead)
            allXP = allXP + XPsAfterHead
            
        if end1 < end:
            restXP = allMaxXP_recursive(end1+1, end, d, checkNohead)
            allXP = allXP + restXP
            
        return allXP

    @staticmethod
    def allSpecXP(sentence, start: int, end: int, d: list[int], XPtest) -> list[tuple[int, int, int]]:
        '''
        a start…end tartományba eső összes CP-t adja vissza rekurzívan*/
        visszaadott érték: az összes CP listája a tartományban: [(XPstart, XPhead, XPend), …] */
        csak akkor kerül a listára egy XP, ha a cp(start, head, end, d) függvény igaz értéket ad vissza */
        
        
        - sentence: a mondat reprezentációja, az XPtest ez alapján ellenőrzi, hogy megfelelő-e az XP
        - start: kezdő index
        - end: végső index
        - d: a függőségi élek listája
        - XPtest: függvény, ami ellenőrzi, hogy az (s,h,e) XP megfelelő-e.
            Csak a megfelelő XP-k kerülnek visszaadásra.
            Az XPtest 5 argumentumú függvény
            - sentence
            - s
            - h
            - e
            - d
            Az XPtest igazságértéket ad vissza eredményül
        '''
        
        allXP = []
        
        if start == end:
            (start1, head1, end1) = (start, start, end)
        else:
            (start1, head1, end1) = firstMaxXP(start,end,d)
        
        if XPtest(sentence, start1, head1, end1, d):
            allXP = [(start1, head1, end1)]
        
        if start1 < head1:
            XPsBeforeHead = allSpecXP(sentence, start1, head1-1, d, XPtest)
            allXP = allXP + XPsBeforeHead
        
        if head1 < end1:
            XPsAfterHead = allSpecXP(sentence, head1+1, end1, d, XPtest)
            allXP = allXP + XPsAfterHead
        
        if end1 < end:
            restXP = allSpecXP(sentence, end1+1, end, d, XPtest)
            allXP = allXP + restXP
        
        return allXP

    @staticmethod
    def getDep(dep0:list[tuple[int, int, int]]) -> tuple[dict, dict, list[int]]:
        '''
        '''
        ids = [id for id,_ in dep0]
        deps = [d for _,d in dep0]
        root = [d for d in deps if d not in ids][0]
        dict0 = {i+1:x for i, x in enumerate(ids)}
        dict0[ROOT] = root
        invdict = {x:i+1 for i, x in enumerate(ids)}
        invdict[root] = ROOT
        d = [invdict[id] for id in deps]
        return dict0, invdict, d   

    @staticmethod
    def CPtest(sentence, start, head, end, deps):
        return sentence[head-1]['upostag'] == 'VERB'
