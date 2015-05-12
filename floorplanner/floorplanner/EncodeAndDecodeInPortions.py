__author__ = 'Filippo'

import fpgaApi as f
import json

def encodeInPortions(fpga):

    fpga.portions=f.createPortions(fpga)
    data={}
    data['name']=fpga.name
    data['portions']=[]
    for p in fpga.portions:
        porData={}
        porData['x1']=p.x
        porData['x2']=p.x2
        porData['type']=p.t
        min,max=fpga.height,0
        for i in xrange(fpga.height):
            if (p.rowsBool[i])and (i<min):
                min=i
            if (p.rowsBool[i])and (i>max):
                max=i
        porData['y1']=min
        porData['y2']=max
        data['portions'].append(porData)
    with open(fpga.name+"_Port.json",'w') as out:
        json.dump(data,out)


def decodeFromPortionsFile(name):
    with open(name,'r') as out:
        j=json.load(out)

    por=j['portions']

    max, may=0,0
    for p in por:
        if (p['x2']>max):
            max=p['x2']
        if (p['y2']>may):
            may=p['y2']

    res=[]
    for i in xrange(may+1):
        res.append(range(max+1))

    for p in por:
        for i in range(p['x1'],p['x2']+1):
            for k in range(p['y1'],p['y2']+1):
                res[k][i]= f.block(i,k,p['type'])

    fpga = f.board(j['name'],max+1,may+1)
    fpga.blocks= res
    return fpga


'''
with open('data2.txt', 'r') as outfile:
    j=json.load(outfile)
j= j[0]

fpga = f.board(j["name"],j["width"],j["height"])

blocks = j["blocks"]

for b in blocks:
    fpga.addBlock(f.block(b.get("x"),b.get("y"),b.get("t")))

fpga.blocks = f.rearrange(fpga,fpga.blocks)
encodeInPortions(fpga)

fpga = decodeFromPortionsFile(fpga.name+"_Port.json")
print fpga.height,fpga.width,fpga.blocks[55][4]
'''