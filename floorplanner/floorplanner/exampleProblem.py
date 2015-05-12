"""
@author Marco Rabozzi [marco.rabozzi@mail.polimi.it]
"""


with open('floorplanner/fpga/5SEEBF45I3.json') as f:
	fpga = eval(f.read())

with open('floorplanner/floorplanner/problem.json') as f:
	problem = eval(f.read())

print problem

import FPGAALteraToRabozziFormat as decode
import floorplanner


fpga=decode.decodeFPGAAltera('5SEEBF45I3')
res= floorplanner.solve(problem, fpga, False, None)

res = decode.solutionToReal('5SEEBF45I3',res)
print res
import json

with open('js/result.json','w') as o:
    json.dump(res,o)