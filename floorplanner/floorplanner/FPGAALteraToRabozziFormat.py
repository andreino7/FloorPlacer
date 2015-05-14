
def decodeFPGAAltera(name,prec):

    import json
    import fpgaApi as f

    import EncodeAndDecodeInPortions as enc

    fpga = enc.decodeFromPortionsFile('floorplanner/floorplanner/'+name+'_Port.json')

    json_blocks=[]


    #fpga.blocks = f.rearrange(fpga,fpga.blocks)
    f.shrink(fpga,prec)
    f.shrinkWidth(fpga,3)

    res={}
    for r in fpga.blocks:
        for b in r:
            if not(b.t in res.keys()):
                res[b.t]={}
                res[b.t]['total']=0
                res[b.t]['number']=1
            res[b.t]['total']+=b.d*b.l

    mat=[]
    for r in fpga.blocks:
        for b in r:
            mat.append({'x':b.x,'y':b.y,'t':b.t,'d':b.d,'l':b.l})

    data = {'name':fpga.name, 'maxTY': fpga.height, 'resources':res, 'maxTX':fpga.width, "tileH" : 20, "tileW" : 2, "FFxCLB" : 8, "LUTxCLB" : 8, 'matrix':mat }

    return data
    '''
    with open(fpga.name +'_prova.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys = True, indent = 4, ensure_ascii=False)
    '''

def solutionToReal(name,solution,prec):
    import copy
    import fpgaApi as f
    import EncodeAndDecodeInPortions as enc
    real={}
    real = copy.deepcopy(solution)
    fpga = enc.decodeFromPortionsFile('floorplanner/floorplanner/'+name+'_Port.json')
    f.shrink(fpga,prec)
    f.shrinkWidth(fpga,3)

    for r in real['regions'].keys():
        real['regions'][r]['x1']= f.realx(fpga.blocks,real['regions'][r]['x1'],real['regions'][r]['y1'])
        real['regions'][r]['x2']= f.realx(fpga.blocks,real['regions'][r]['x2'],real['regions'][r]['y2'])+fpga.blocks[solution['regions'][r]['y2']][solution['regions'][r]['x2']].l-1
        real['regions'][r]['y1']= f.realy(fpga.blocks,solution['regions'][r]['x1'],real['regions'][r]['y1'])
        real['regions'][r]['y2']= f.realy(fpga.blocks,solution['regions'][r]['x2'],real['regions'][r]['y2'])+fpga.blocks[solution['regions'][r]['y2']][solution['regions'][r]['x2']].d-1

    return real