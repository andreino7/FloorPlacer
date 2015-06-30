"""
@author Marco Rabozzi [marco.rabozzi@mail.polimi.it]
"""
PRECISIONS=[21,13,9]


with open('floorplanner/floorplanner/problem.json') as f:
	problem = eval(f.read())

print problem

import FPGAALteraToRabozziFormat as decode
import multiThreadFloorplanner as floorplanner

if 'precision' in problem.keys():
	prec = int(problem['precision'])
else:
    prec=0

fpga=decode.decodeFPGAAltera(problem['fpga'],PRECISIONS[prec])
res= floorplanner.solve(problem, fpga, False, None)
if not res == "Unfeasible":
    res = decode.solutionToReal(problem['fpga'],res,PRECISIONS[prec])
print res
import json

with open('js/result.json','w') as o:
    json.dump(res,o)