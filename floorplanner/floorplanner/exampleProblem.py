"""
@author Marco Rabozzi [marco.rabozzi@mail.polimi.it]
"""
PRECISIONS=[10,15,30]

with open('floorplanner/fpga/5SEEBF45I3.json') as f:
	fpga = eval(f.read())

with open('floorplanner/floorplanner/problem.json') as f:
	problem = eval(f.read())

print problem

import FPGAALteraToRabozziFormat as decode
import floorplanner

if 'precision' in problem.keys():
	prec = int(problem['precision'])
else:
    prec=0

fpga=decode.decodeFPGAAltera('5SEEBF45I3',PRECISIONS[prec])
res= floorplanner.solve(problem, fpga, False, None)

res = decode.solutionToReal('5SEEBF45I3',res,PRECISIONS[prec])
print res
import json

with open('js/result.json','w') as o:
    json.dump(res,o)