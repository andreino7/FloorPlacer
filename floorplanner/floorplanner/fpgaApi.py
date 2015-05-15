# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 13:10:50 2015

@author: Filippo
"""
#IMPORTANT NonRec must be Last
types= ['DSP','LAB','MK20','NonRec']


class block:
    def __init__(self, x,y,t):
        self.x=x
        self.y=y
        self.t=t
        self.d=1
        self.l=1
    
            

class board:
    def __init__(self, name,width,height):
        self.width = width
        self.height = height 
        self.name = name
        self.blocks = []
        self.portions=[]
    def addBlock(self,block):
        self.blocks.append(block)
        
    def changeColumnTo(self, c,t):
        for b in self.blocks:
            if b.x == c:
                b.t = t
    def changeBlockTo(self,x,y,t):
        for b in self.blocks:
            if b.x==x and b.y==y:
                b.t=t
    

class portion:
    def __init__(self,x,x2,rowsBool,t):
        self.x = x
        self.x2 = x2
        self.rowsBool = rowsBool
        self.t = t
        self.rowDepth=1

def pop(lista,i):
    res = lista[i]
    del lista[i]
    return res

def find(lista,x,y):
    for b in range(len(lista)):
        if lista[b].x==x and lista[b].y==y:
            return pop(lista,b)
      
def mostType(l):
    num={}
    for t in types:
        num.update({t:0})
    
    for b in l:
        num[b.t]+=1
    m=0
    res=''
    
    for t in types:
        if (num[t]>=m):
            res = t
            m=num[t]
    
    return res        

def nOfType(l,t):
    res=0
    for b in l:
        if (b.t==t):
            res+=1
    return res

       
def shrink(fpga,factor):
      res=[]
      for i in range(factor):
          res.append(range(fpga.width))
      medium_dens= fpga.height/factor 
      #fpga.blocks=rearrange(fpga,fpga.blocks)
      for i in range(fpga.width):
          for j in range(factor):
              bigBlock = []#fpga.blocks[int(round(j*medium_dens)):int(round((j+1)*medium_dens))][i]
              for k in range(int(round(j*medium_dens)),int(round((j+1)*medium_dens))):
                  bigBlock.append(fpga.blocks[k][i])
              predominantType= mostType(bigBlock)
              bb=block(i,j,predominantType)
              bb.d=nOfType(bigBlock,predominantType)
              res[j][i]=bb        
      fpga.blocks= res   
      fpga.height = factor        
      
import copy

def createPortion2(fpga,blocks,height):
    starter=None
    
    notFound=True     
    i,j=0,0
    while i<fpga.height and notFound:
        j=0
        while j<fpga.width and notFound:
            if not(blocks[i][j] is  None):
                starter = copy.copy(blocks[i][j])
                notFound=False
            j+=1
        i+=1
    
    if starter==None:
        return None
           
    inPort = [starter]    
    toExplore = [starter]

    while toExplore != []:
        exp = pop(toExplore,0)
        i=1
        stop=False
        while exp.x+i<fpga.width and not stop:
            if not(blocks[exp.y][exp.x+i] is None):
                if blocks[exp.y][exp.x+i].t==exp.t:
                    i+=1
                else:
                    stop=True
            else:
                stop=True

        stop=False
        j=1
        while exp.y+j<fpga.height and not stop:
            for k in range(i):
                if blocks[exp.y+j][exp.x+k]!=None:
                    if blocks[exp.y+j][exp.x+k].t!=exp.t:
                        stop=True
                else:
                    stop=True
            if not stop:
                j+=1
        for k in range(i):
            for z in range(j):
                t= copy.copy(blocks[exp.y+z][exp.x+k])
                blocks[exp.y+z][exp.x+k]=None
                if (t!=None):
                    inPort.append(t)

    miny,minx= inPort[0].y,inPort[0].x
    maxy=0
    maxx=0
    for b in inPort:
        if (b.x > maxx):
            maxx=b.x
        if (b.x< minx):
            minx=b.x
        if (b.y> maxy):
            maxy=b.y
        if (b.y<miny):
            miny=b.y
    mat = {}
    for i in range(height):
        if (i<=maxy) and i >=miny:
            mat.update({i:True})
        else:
            mat.update({i:False})
    tp=inPort[0].t
    return portion(minx,maxx,mat,tp)                      
                

     
                
                


def rearrange(fpga,blocks):
    res=[]
    for i in range(fpga.height):
        res.append(range(fpga.width))
     
    for b in blocks:
        res[b.y][b.x] = b
    
    
    return res    

def createPortions(fpga):
    bs= copy.deepcopy(fpga.blocks)
    res=[]
    finished=False
    while not finished:
        new = createPortion2(fpga,bs,fpga.height)
        if new!=None:
            res.append(new)
            #print(bs[55][4])
            #print (new.x,new.x2,new.t,new.rowsBool)
        else:
            finished=True
        
    
    return res  

def minDepth(listOfBlocks):
    """

    :rtype : int
    """
    min=listOfBlocks[0].d
    for i in range(1,len(listOfBlocks)):
        if listOfBlocks[i].d<min:
            min=listOfBlocks[i].d
    return min

def minLen(listOfBlocks):
    """

    :rtype : int
    """
    min=listOfBlocks[0].l
    for i in range(1,len(listOfBlocks)):
        if listOfBlocks[i].l<min:
            min=listOfBlocks[i].l
    return min



def shrinkWidth(fpga,maxW):
    res=range(fpga.height)
    maxH=fpga.height

    for i in range(fpga.height):
        res[i]=[]
    for r in range(fpga.height):
        c=0
        while c<fpga.width:
            same=0
            union=[fpga.blocks[r][c]]
            k=1
            diff = False
            while k<maxW and c+k<fpga.width and not diff:
                z=0
                while z<maxH and not diff:
                    if (fpga.blocks[z][c].t!=fpga.blocks[z][c+k].t):
                        diff=True
                    z+=1
                if not diff:
                    same=k
                    k+=1



            if same!=0:
                new = block(len(res[r]),r,fpga.blocks[r][c].t)
                new.d= minDepth(union)
                new.l=same+1
                res[r].append(new)
            else:
                new = block(len(res[r]),r,fpga.blocks[r][c].t)
                new.d=fpga.blocks[r][c].d
                new.l=1
                res[r].append(new)
            c+=same+1
    fpga.blocks=res
    mW=0
    for i in range(fpga.height):
        if len(res[i])>mW:
            mW=len(res[i])
    for i in range(fpga.height):
        if len(res[i])<mW:
            for k in range(mW-len(res[i])):
                nb=block(len(res[i]),i,types[-1])
                nb.d=0
                nb.l=0
                res[i].append(nb)



    fpga.width = mW

def shrinkHeight(fpga,maxH):
    res=range(fpga.width)

    for i in range(fpga.width):
        res[i]=[]
    for c in range(fpga.width):
        r=0
        while r<fpga.height:
            same=0
            union=[fpga.blocks[r][c]]
            for k in range(1,maxH):
                if (r+k)<fpga.height and (fpga.blocks[r+k][c].t==fpga.blocks[r][c].t) and (fpga.blocks[r+k][c].l==fpga.blocks[r][c].l):
                    same=k
                    union.append(fpga.blocks[r+k][c])
                else:
                    break

            if same!=0:
                new = block(c,len(res[c]),fpga.blocks[r][c].t)
                new.l= minLen(union)
                new.d=same+1
                res[c].append(new)
            else:
                new = block(c,len(res[c]),fpga.blocks[r][c].t)
                new.l=fpga.blocks[r][c].l
                new.d=1
                res[c].append(new)
            r+=same+1
    mH=0
    for i in range(fpga.width):
        if len(res[i])>mH:
            mH=len(res[i])

    for i in range(fpga.width):
        if len(res[i])<mH:
            res[i].append(block(i,mH-1,types[-1]))

    resTrasp = range(mH)

    for i in range(mH):
        resTrasp[i]=range(fpga.width)

    for i in xrange(fpga.width):
        for j in xrange(mH):
            resTrasp[j][i]=res[i][j]


    fpga.blocks=resTrasp

    fpga.height=mH
        

def prepareForFloorplanning(fpga):
    shrink(fpga,10)
    fpga.portions= createPortions(fpga)
    shrinkWidth(fpga,5)
    

class region:
    def __init__(self, requirements):
        self.requirements=requirements

def realx(blocks,x,y):
    rx=0
    for i in range(x):
        rx+=blocks[y][i].l
    return rx
def realy(blocks,x,y):
    ry=0
    for i in range(y):

        ry+=blocks[i][x].d
    return ry
def deshrink(fpga):
    res=[]
    max,may=0,0

    for r in xrange(0,fpga.height):

        for c in xrange(0,fpga.width):
            ci= realx(fpga.blocks,c,r)
            ri= realy(fpga.blocks,c,r)
            for i in xrange(fpga.blocks[r][c].d):
                for j in xrange(fpga.blocks[r][c].l):
                    res.append(block(ci+j,ri+i,fpga.blocks[r][c].t))
                    if (ci+j>max):
                        max=ci+j
                    if ri+i>may:
                        may=ri+i




    fpga.blocks=res
    fpga.height=may+1
    fpga.width=max+1
    fpga.blocks= rearrange(fpga,fpga.blocks)

