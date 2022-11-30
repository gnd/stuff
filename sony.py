#!/usr/bin/python3
# extended https://github.com/erik-smit/sony-camera-api/blob/master/liveView.py

import http.client
import struct
import binascii
import pprint

import pygame
import time
import io

from numpy import *

In=1
pygame.init()
### TODO - get current screen resolution
screen_width = 1920
screen_height = 1080
size=(screen_width,screen_height)
screen = pygame.display.set_mode(size, pygame.RESIZABLE, display=0) 

conn = http.client.HTTPConnection("192.168.122.1:60152")
# http://192.168.122.1:60152/liveview.JPG?!1234!http-get:*:image/jpeg:*
conn.request("GET", "/liveview.JPG?%211234%21http%2dget%3a%2a%3aimage%2fjpeg%3a%2a%21%21%21%21%21")
res = conn.getresponse()

def set_transparent(r,g,b):
  if r < 100:
    return (0,0,0)

set_transparent_v = vectorize(set_transparent)

done = False
colorkey = False
while not done:
  for event in pygame.event.get():
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        done = True
        break
      if event.key == pygame.K_K:
        if colorkey:
          colorkey = False
        else:
          colorkey = True
    elif event.type == pygame.QUIT:
        done = True
        break
  if done:
    break

  # draw some background
  background = pygame.image.load('back.png')
  background = pygame.transform.scale(background, size)
  screen.blit(background,(0,0))

  # get some jpeg data from the action cam
  commonHeaderLength = 1 + 1 + 2 + 4
  commonHeader = res.read(commonHeaderLength)

  payloadHeaderLength = 4 + 3 + 1 + 4 + 1 + 115
  payloadHeader = res.read(payloadHeaderLength)

  jpegSize = struct.unpack('>i','\x00'.encode()+payloadHeader[4:7])[0]
  paddingSize = ord(payloadHeader[7:8])
 
  jpegData = res.read(jpegSize)
  paddingData = res.read(paddingSize)

  # load image from stream
  img = pygame.image.load(io.BytesIO(jpegData))

  if colorkey:
    # mark some pixels as black
    pixels = pygame.surfarray.pixels3d(img)
    #set_transparent_v(pixels)
    for i in range(640):
      for j in range(360):
        if pixels[i,j,0] < 100:
           pixels[i,j] = (0,0,0)

    # free the surfarray
    del pixels

	# set colorkey
    img.set_colorkey((0,0,0))


  # resize, and draw
  img = pygame.transform.scale(img, size).convert()
  screen.blit(img,(0,0)) 

  # flip the buffers
  pygame.display.flip()
