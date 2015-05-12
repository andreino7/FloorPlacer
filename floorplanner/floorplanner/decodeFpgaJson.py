# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 17:33:36 2015

@author: Filippo
"""

import os, sys, pygame
from pygame.locals import *
import fpgaApi as f



      

types= ['DSP','LAB','MK20','NonRec']

WHITE = 255,255,255
GREEN = 0,255,0
BLACK = 0,0,0
BLUE  = 0,0,255
RED   = 255,0,0
YELLOW   = 0,255,255

colors = {'DSP':GREEN,'LAB':RED,'MK20':BLUE,'NonRec':WHITE }




        

class board:
    def __init__(self, name,width,height):
        self.width = width
        self.height = height 
        self.name = name
        self.blocks = []
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
    
class blockView:
    def __init__(self, b,r):
        self.b=b
        self.r=r
X0 = 0
Y0 = 0

XOFF = 20
YOFF = 20


import json
import EncodeAndDecodeInPortions as enc

fpga = enc.decodeFromPortionsFile("5SEEBF45I3_Port.json")
'''
f.shrink(fpga,10)
f.shrinkWidth(fpga,3)
'''

regDic={}

with open('result.json','r') as infile:
    sol = json.load(infile)
regDic= sol['regions']
regions=[]

for r in regDic.values():
    regions.append(r)
#print regions[0].y1 ,regions[0].y2

size = width, height = 800 , 600
screen = pygame.display.set_mode(size)
pygame.display.set_caption("pygame.draw functions ~ examples")
pygame.init()
   

bviews = []
modes=['Single','Column']
seltype=types[0]
selmode='Single'

BW = 8
BH = 10

myfont = pygame.font.SysFont("monospace", 10)


configuring = True

while configuring:
    
    screen.fill(BLACK)
    
   

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.display.quit()
            sys.exit(0)
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            pygame.display.quit()
            sys.exit(0)
        elif event.type == KEYDOWN and event.key == K_z:
            BW+=1
            BH+=1
        elif event.type == KEYDOWN and event.key == K_x:
            BW-=1
            BH-=1  
        elif event.type == KEYDOWN and event.key == K_c:
            selmode='Column'     
        elif event.type == KEYDOWN and event.key == K_s:
            selmode='Single'       
        elif event.type == KEYDOWN and event.key == K_d:
            seltype='DSP'   
        elif event.type == KEYDOWN and event.key == K_m:
            seltype='MK20'     
        elif event.type == KEYDOWN and event.key == K_n:
            seltype='NonRec'
        elif event.type == KEYDOWN and event.key == K_l:
            seltype='LAB'     
        elif event.type == KEYDOWN and event.key == K_RIGHT:
            X0-=BW  
        elif event.type == KEYDOWN and event.key == K_LEFT:
            X0+=BW      
        elif event.type == KEYDOWN and event.key == K_UP:
            Y0-=BH  
        elif event.type == KEYDOWN and event.key == K_DOWN:
            Y0+=BH     
        elif event.type == KEYDOWN and event.key == K_RETURN:
            configuring = False    

        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
      # get a list of all sprites that are under the mouse cursor
            clicked_sprites = [s for s in bviews if s.r.collidepoint(pos)] 
            if clicked_sprites != []:
                if selmode=='Column':
                    fpga.changeColumnTo(clicked_sprites[0].b.x , seltype)
                else:
                    fpga.changeBlockTo(clicked_sprites[0].b.x,clicked_sprites[0].b.y,seltype)
    
    p=pygame.mouse.get_pos()
     
    bviews=[]
        
    
        
    for i in range(fpga.height):
        for j in range(fpga.width):

            b = fpga.blocks[i][j]
            if isinstance(b,f.block):
                pygame.draw.rect(screen, colors.get(b.t), (XOFF+ X0 + b.x*BW,YOFF + Y0 + b.y*BH,BW,BH), 0)
                bviews.append(blockView(b, pygame.draw.rect(screen, BLACK, (XOFF+ X0 + b.x*BW,YOFF + Y0 + b.y*BH,BW,BH), 1)))

    for r in regions:
        print r
        pygame.draw.rect(screen,YELLOW,(XOFF+ X0 + r['x1']*BW,YOFF + Y0 + r['y1']*BH,BW*(r['x2']-r['x1']+1),BH*(r['y2']-r['y1']+1)))
     
    over = [s for s in bviews if s.r.collidepoint(p)]
    if over != []:
        text = myfont.render("(" + str(over[0].b.x) + ", " + str(over[0].b.y) + ")" + " Mode: "+ selmode + "  TypeSel: "+seltype , True, WHITE)
        screen.blit(text,(0,0))    
    
    pygame.display.flip() 
    pygame.time.delay(100)
            

            