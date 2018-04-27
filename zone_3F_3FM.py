import sys
import pandas as pd
import pygame
from pygame.locals import *
import math
import copy

WINWIDTH = 1230
WINHEIGHT = 890
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

TILEWIDTH = 5
TILEHEIGHT = 8

FPS = 30 # frames per second to update the screen
BRIGHTBLUE = (  0, 170, 255)
WHITE      = (255, 255, 255)
BLUE       = (  0,   0, 255) 
BGCOLOR = WHITE
#TEXTCOLOR = (180, 180, 180)
TEXTCOLOR = BRIGHTBLUE

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


def main():
    global FPSCLOCK
    global DISPLAYSURF
    global IMAGESDICT
    global TILEMAPPING
    global BASICFONT
    global FLOORNAMEFONT
    global ZONENAMEFONT

    # Pygame initialization and basic set up of the global variables.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))

    pygame.display.set_caption('Zone Picking')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    FLOORNAMEFONT = pygame.font.Font('freesansbold.ttf', 60)
    ZONENAMEFONT = pygame.font.Font('freesansbold.ttf', 90)

    # A global dict value that will contain all the Pygame
    # Surface objects returned by pygame.image.load().
    IMAGESDICT = {'title': pygame.image.load('images5x8/title.png'),
                  'lots': pygame.image.load('images5x8/5x8_lot.png'),
                  'floor': pygame.image.load('images5x8/5x8_floor.png'),
                  'lots_1_ss': pygame.image.load('images5x8/5x8_lot_1_ss.png'),
                  'lots_2_ss': pygame.image.load('images5x8/5x8_lot_2_ss.png'),
                  'lots_3_ss': pygame.image.load('images5x8/5x8_lot_3_ss.png'),
                  'lots_4_ss': pygame.image.load('images5x8/5x8_lot_4_ss.png'),
                  'lots_5_ss': pygame.image.load('images5x8/5x8_lot_5_ss.png'),
                  'lots_1_batched': pygame.image.load('images5x8/5x8_lot_1_batched.png'),
                  'lots_2_batched': pygame.image.load('images5x8/5x8_lot_2_batched.png'),
                  'lots_3_batched': pygame.image.load('images5x8/5x8_lot_3_batched.png'),
                  'lots_4_batched': pygame.image.load('images5x8/5x8_lot_4_batched.png'),
                  'lots_5_batched': pygame.image.load('images5x8/5x8_lot_5_batched.png'),
                  # 'path_L_U_D': pygame.image.load('path_1.png'),
                  # 'path_L_D': pygame.image.load('path_2.png'),
                  # 'path_R_D': pygame.image.load('path_3.png'),
                  # 'path_L_U': pygame.image.load('path_4.png'),
                  # 'path_R_U': pygame.image.load('path_5.png'),
                  # 'path_R_U_D': pygame.image.load('path_6.png'),
                  # 'path_L_R_D': pygame.image.load('path_7.png'),
                  # 'path_L_R_U': pygame.image.load('path_8.png'),
                  # 'path_L_R_U_D': pygame.image.load('path_9.png'),
                 }

    # These dict values are global, and map the character that appears
    # in the zone_map file to the Surface object it represents.
    TILEMAPPING = {'#': IMAGESDICT['lots'],
                   '.': IMAGESDICT['floor'],
                   'a': IMAGESDICT['lots_1_ss'],
                   'b': IMAGESDICT['lots_2_ss'],
                   'c': IMAGESDICT['lots_3_ss'],
                   'd': IMAGESDICT['lots_4_ss'],
                   'e': IMAGESDICT['lots_5_ss'],
                   '1': IMAGESDICT['lots_1_batched'],
                   '2': IMAGESDICT['lots_2_batched'],
                   '3': IMAGESDICT['lots_3_batched'],
                   '4': IMAGESDICT['lots_4_batched'],
                   '5': IMAGESDICT['lots_5_batched'],
                  }

    # read the zone maps
    zones_3F = read_zone_file('3F_zone_maps.txt')
    zones_3FM = read_zone_file('3FM_zone_maps.txt')
    floor_name = [zones_3F['floor_name'], zones_3FM['floor_name']]
    # read the data of locations, including the aisle, bay values of a location
    locations_df = {}
    locations_df['3F'] = pd.read_csv('locations_3F.csv', index_col = 0)
    locations_df['3FM'] = pd.read_csv('locations_3FM.csv', index_col = 0)
    # read the time-dependent shipments changes
    ss_logs = read_shipments_batchs_logs('shipments_batchs_logs.txt')
        # key = timestamp
        # values = {'ppid': [ ], 'sequence': [ , , ], 'batch': [ , , ]}

    # currently, we show all picking zones in 3F & 3FM
    mapObj = [zones_3F['map_obj'], zones_3FM['map_obj']]
    mapObj_initial = copy.deepcopy(mapObj)
    start_screen(mapObj) # show the title screen until the user presses a key

    # timestamp
    timestamps = sorted(list(ss_logs.keys()))

    ss_index = 0 # first timestamp of shipments
    ss_length = len(ss_logs)

    # The main game loop
    while True: # main game loop
        # Run to actually show the zone map:
        timestamp = timestamps[ss_index]
        ppid = ss_logs[timestamps[ss_index]]['ppid'] # the ppid
        shipments = ss_logs[timestamps[ss_index]]['sequence'] # the list of shipments pending to be batched
        batchs = ss_logs[timestamps[ss_index]]['batch']  # the list of shipments batched
        
        result = run_zone(mapObj_initial, floor_name, locations_df, timestamp, ppid, shipments, batchs, ss_length)

        if result == 'next':
            # Go to the next level.
            ss_index += 1
            if ss_index >= ss_length:
                # If there are no more timestamp, go back to the first one.
                ss_index = 0
        elif result == 'back':
            # Go to the previous level.
            ss_index -= 1
            if ss_index < 0:
                # If there are no previous levels, go to the last one.
                ss_index = ss_length-1

        elif result == 'reset':
            start_screen(mapObj_initial)
            pass # Do nothing. Loop re-calls run_zone() to reset the zone


def run_zone(mapObj_initial, floor_name, locations_df, timestamp, ppid, shipments, batchs, ss_length):
    # height of each mapObj
    height_mapObj = [len(obj) for obj in mapObj_initial]
    interval = 60 # the distance between 3F bottom and 3FM top
    # batchsize
    batchsize = len(batchs)
    mapNeedsRedraw = True

    while True: # main game loop
        # Reset these variables:

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                # Handle key presses
                if event.key == K_LEFT:
                    time_change = LEFT
                elif event.key == K_RIGHT:
                    time_change = RIGHT
                elif event.key == K_ESCAPE:
                    terminate() # Esc key quits.
                elif event.key == K_n:
                    return 'next'
                elif event.key == K_b:
                    return 'back'
                elif event.key == K_r:
                    return 'reset' # Reset the zone map.

        mapObj_3F, changed_3F = update_map(mapObj_initial[0], locations_df['3F'], shipments, batchs)
        mapObj_3FM, changed_3FM = update_map(mapObj_initial[1], locations_df['3FM'], shipments, batchs)

        if changed_3F or changed_3FM:
            mapNeedsRedraw = True

        if mapNeedsRedraw:
            mapSurf_3F = draw_map(mapObj_3F)
            mapSurf_3FM = draw_map(mapObj_3FM)
            mapNeedsRedraw = False

            DISPLAYSURF.fill(BGCOLOR)

            # Adjust mapSurf's Rect object
            mapSurfRect_3F = mapSurf_3F.get_rect()
            mapSurfRect_3F.midtop = (HALF_WINWIDTH, 60)
            mapSurfRect_3FM = mapSurf_3FM.get_rect()
            mapSurfRect_3FM.midbottom = (HALF_WINWIDTH, WINHEIGHT - 10)
            # Draw mapSurf to the DISPLAYSURF Surface object.
            DISPLAYSURF.blit(mapSurf_3F, mapSurfRect_3F)
            DISPLAYSURF.blit(mapSurf_3FM, mapSurfRect_3FM)

            # Draw  floor name to the DISPLAYSURF Surface object
            for i in range(len(floor_name)):
                height = sum(height_mapObj[:i])
                zoneSurf = BASICFONT.render('Floor: {} '.format(floor_name[i]), 1, TEXTCOLOR)
                zoneRect = zoneSurf.get_rect()
                zoneRect.topleft = (20,  10 + height*TILEHEIGHT + i * interval)
                DISPLAYSURF.blit(zoneSurf, zoneRect)

            draw_border_3FM(mapObj_initial[1])

            stepSurf = BASICFONT.render('{}, PPID: {}, batchjobsize: {}'.format(timestamp, ppid, batchsize), 1, TEXTCOLOR)
            stepRect = stepSurf.get_rect()
            stepRect.topleft = (20, 30)
            DISPLAYSURF.blit(stepSurf, stepRect)

            pygame.display.update() # draw DISPLAYSURF to the screen
        FPSCLOCK.tick()


def update_map(mapObj_initial, locations_df, shipments, batchs):
    # update the shipments in the zone map
    mapObj = copy.deepcopy(mapObj_initial)

    # e.g. 'sequence': [176653, 176062, 180793], 'batch': [176265, 175953, 175996, 176166]
    if shipments: # if there are shipments (ready to pick) in the zone map 
        # update the map
        for i in range(len(shipments)):
            if shipments[i] in locations_df.index:
                location = locations_df.loc[shipments[i]]
                zone = location['zone']
                aisle = location['aisle']
                bay = location['bay']

                y, x = location_xy(zone, aisle, bay)

                if mapObj[x][y] == '#': # the (x, y) position is a 'lot'
                    mapObj[x][y] = 'a'
                elif mapObj[x][y] == 'a':
                    mapObj[x][y] = 'b'
                elif mapObj[x][y] == 'b':
                    mapObj[x][y] = 'c'
                elif mapObj[x][y] == 'c':
                    mapObj[x][y] = 'd'
                elif mapObj[x][y] == 'd':
                    mapObj[x][y] = 'e'

        if batchs: 
            # update the batched shipments in the map
            for i in range(len(batchs)):
                if batchs[i] in locations_df.index:
                    location = locations_df.loc[batchs[i]]
                    zone = location['zone']
                    aisle = location['aisle']
                    bay = location['bay']

                    y, x = location_xy(zone, aisle, bay)

                    if mapObj[x][y] in ('#','a','b','c','d','e'):
                        mapObj[x][y] = '1'
                    elif mapObj[x][y] == '1':
                        mapObj[x][y] = '2'
                    elif mapObj[x][y] == '2':
                        mapObj[x][y] = '3'
                    elif mapObj[x][y] == '3':
                        mapObj[x][y] = '4'
                    elif mapObj[x][y] == '4':
                        mapObj[x][y] = '5'

        return mapObj, True # the map needs to redraw

    return mapObj, False # the map doesn't need to redraw


def read_zone_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    h = len(lines) #
    w = len(lines[0].rstrip().split(' ')) #
    # Convert maps to a 2-d array map object
    map_obj = []
    for x in range(h):
        map_obj.append(lines[x].rstrip().split(' '))

    floor_name = filename.split('_')[0]
    zones = {'floor_name': floor_name,
             'height': h,
             'width': w,
             'map_obj': map_obj,
            }
    return zones


def read_shipments_batchs_logs(filename):
    ss_batchs = {}

    with open(filename, 'r') as f:
        lines = f.readlines()

    for i in range(len(lines)):
        line = lines[i].rstrip('\r\n').split(',')
        batch_index = line.index(';')
        ss_batchs[line[0]] = {'ppid': int(line[1]),
                              'sequence': [int(x) for x in line[2: batch_index]],
                              'batch': [int(x) for x in line[batch_index+1:]]
                             }    

    return ss_batchs


def draw_map(mapObj):
    """Draws the zone map to a Surface object, including the Locations . 
    This function does not call pygame.display.update()"""

    # mapSurf will be the single Surface object that the tiles are drawn
    # on, so that it is easy to position the entire map on the DISPLAYSURF
    # Surface object
    map_h = len(mapObj)
    map_w = len(mapObj[0])

    mapSurfWidth = map_w * TILEWIDTH
    mapSurfHeight = map_h * TILEHEIGHT
    mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
    mapSurf.fill(BGCOLOR) # start with a blank color on the surface

    # Draw the tile sprites onto this surface
    for h in range(map_h):
        for w in range(map_w):
            spaceRect = pygame.Rect((w * TILEWIDTH, h * TILEHEIGHT, TILEWIDTH, TILEHEIGHT))
            if mapObj[h][w] in TILEMAPPING:
                baseTile = TILEMAPPING[mapObj[h][w]]

            # First draw the base ground/wall tile
            mapSurf.blit(baseTile, spaceRect)

    return mapSurf


def location_xy(zone, aisle, bay):
    # from the zone, aisle, bay to get the (x, y) position in the zone maps
    # here only support the zones in DEO1 3FM 
    # remeber to transpose the x, y values
    tile_x = 0
    tile_y = 0
    if zone == 'A':
        tile_x = aisle * 3 - 1
        if bay <= 16:
            tile_y = math.ceil(bay/2) - 1
        elif bay <= 32:
            tile_y = math.ceil(bay/2) 
        elif bay <= 56:
            tile_y = math.ceil(bay/2) + 2
        else:
            tile_y = math.ceil(bay/2) + 6
    elif zone == 'AR':
        tile_x = aisle * 2 + 11
        tile_y = math.ceil(bay/2)      
    elif zone == 'B':
        if aisle == 0: # B0
            tile_x = aisle * 3 + 23
            if bay <= 16:
                tile_y = math.ceil(bay/2) - 1
            elif bay <= 32:
                tile_y = math.ceil(bay/2) 
            elif bay <= 56:
                tile_y = math.ceil(bay/2) + 2
            else:
                tile_y = math.ceil(bay/2) + 6
        elif aisle == 1 or aisle == 2: # B1, B2
            tile_x = aisle * 3 + 23
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle == 3: # B3
            if bay%2 == 1:
                tile_x = aisle * 3 + 23
            else:
                tile_x = aisle * 3 + 26
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle > 3 and aisle < 11: # B4 ~ B10
            tile_x = aisle * 3 + 26
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle == 11: # B11
            if bay%2 == 1:
                tile_x = aisle * 3 + 26
            else:
                tile_x = aisle * 3 + 29
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle > 11 and aisle < 20: # B12 ~ B19
            tile_x = aisle * 3 + 29
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle == 20: # B20
            if bay%2 == 1:
                tile_x = aisle * 3 + 29
            else:
                tile_x = aisle * 3 + 31
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
    elif zone == 'C':
        tile_x = aisle * 3 + 94
        if aisle < 18:
            if bay <= 16:
                tile_y = math.ceil(bay/2) + 8
            elif bay <= 40:
                tile_y = math.ceil(bay/2) + 10
            else:
                tile_y = math.ceil(bay/2) + 14
        elif aisle == 18:
            if bay <= 16:
                tile_y = math.ceil(bay/2) - 1
            elif bay <= 32:
                tile_y = math.ceil(bay/2) 
            elif bay <= 56:
                tile_y = math.ceil(bay/2) + 2
            else:
                tile_y = math.ceil(bay/2) + 6 
    elif zone == 'D':
        tile_x = aisle * 3 + 151
        if bay <= 16:
            tile_y = math.ceil(bay/2) - 1
        elif bay <= 32:
            tile_y = math.ceil(bay/2) 
        elif bay <= 56:
            tile_y = math.ceil(bay/2) + 2
        else:
            tile_y = math.ceil(bay/2) + 6
    elif zone == 'E':
        tile_x = aisle * 3 + 178
        if aisle == 0:
            if bay <= 16:
                tile_y = math.ceil(bay/2) - 1
            elif bay <= 32:
                tile_y = math.ceil(bay/2) 
            elif bay <= 56:
                tile_y = math.ceil(bay/2) + 2
            else:
                tile_y = math.ceil(bay/2) + 6
        elif aisle > 0:
            if bay <= 16:
                tile_y = math.ceil(bay/2) - 1
            elif bay <= 32:
                tile_y = math.ceil(bay/2) 
            elif bay <= 52:
                tile_y = math.ceil(bay/2) + 2
            else:
                tile_y = math.ceil(bay/2) + 10
    elif zone == 'F':
        tile_x = aisle * 3 + 208
        if bay <= 16:
            tile_y = math.ceil(bay/2) - 1
        elif bay <= 32:
            tile_y = math.ceil(bay/2) 
        elif bay <= 52:
            tile_y = math.ceil(bay/2) + 2
        else:
            tile_y = math.ceil(bay/2) + 10

    if bay%2 == 1:
        tile_x -= 1
    else:
        tile_x += 1

    return tile_x, tile_y


def start_screen(mapObj):
    # Display the start screen (which has the title and instructions)
    # until the player presses a key. Returns None
    # mapObj = [zones_3F['map_obj'], zones_3FM['map_obj']]

    # Position the title image
    titleRect = IMAGESDICT['title'].get_rect()
    titleRect.top = 10
    titleRect.centerx = HALF_WINWIDTH

    # Start with drawing a blank color to the entire window:
    DISPLAYSURF.fill(BGCOLOR)
    # Draw the title image to the window:
    DISPLAYSURF.blit(IMAGESDICT['title'], titleRect)

    height_mapObj = [len(obj) for obj in mapObj]
    width_mapObj = [len(obj[0]) for obj in mapObj]
    interval = 60 # the distance between 3F bottom and 3FM top
    for i in range(len(mapObj)):
        height = sum(height_mapObj[:i+1])
        mapSurf = draw_map(mapObj[i])
        mapSurfRect = mapSurf.get_rect()
        mapSurfRect.midbottom = (HALF_WINWIDTH, 60 + height*TILEHEIGHT + i * interval)
        # Draw mapSurf to the DISPLAYSURF Surface object
        DISPLAYSURF.blit(mapSurf, mapSurfRect)
    
    # Draw floorname to the DISPLAYSURF Surface object
    floornames = ['3F', '3.5F']
    floor_topleft_xy = {'3F': (20,  10),
                        '3.5F': (20, 10 + height_mapObj[0]*TILEHEIGHT + interval)}
    for i, floorname in enumerate(floornames):
        floor_surf = FLOORNAMEFONT.render('Floor: {} '.format(floorname), 1, (255, 0, 255))
        floor_rect =floor_surf.get_rect()
        floor_rect.topleft = floor_topleft_xy[floorname]
        DISPLAYSURF.blit(floor_surf, floor_rect)

    # Draw zonename to the DISPLAYSURF Surface object
    zonenames = ['A', 'AR', 'B', 'C', 'D', 'E', 'F',]  # zones in 3FM
               #  'G', 'H', 'I', 'J', 'K', 'L', 'LR']  # zones in 3F
    zone_center_xy = {'A': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + 11*TILEWIDTH, 
                                WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2),
                   'AR': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (11+51)/2*TILEWIDTH,
                             WINHEIGHT - 10 - (height_mapObj[1]-5.5)*TILEHEIGHT),
                   'B': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (22+93)/2*TILEWIDTH, 
                            WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2),
                   'C': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (93+150)/2*TILEWIDTH, 
                            WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2),
                   'D': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (150+177)/2*TILEWIDTH, 
                            WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2),
                   'E': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (177+207)/2*TILEWIDTH, 
                            WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2),
                   'F': ((WINWIDTH-width_mapObj[1]*TILEWIDTH)/2 + (207+237)/2*TILEWIDTH, 
                            WINHEIGHT - height_mapObj[1]*TILEHEIGHT/2)}
    for i in range(len(zonenames)):
        zone_surf = ZONENAMEFONT.render(zonenames[i], 1, TEXTCOLOR)
        zone_rect = zone_surf.get_rect()
        zone_rect.center = zone_center_xy[zonenames[i]]
        DISPLAYSURF.blit(zone_surf, zone_rect)

    # Draw borders of zone to the DISPLAYSURF Surface object
    draw_border_3F(mapObj[0])
    draw_border_3FM(mapObj[1])
    
    while True: # Main loop for the start screen.
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return # user has pressed a key, so return.

        # Display the DISPLAYSURF contents to the actual screen.
        pygame.display.update()
        FPSCLOCK.tick()

def draw_border_3F(mapObj):
    # draw the border of zones onto the DISPLAYSURF
    map_h = len(mapObj)
    map_w = len(mapObj[0])

    mapSurfWidth = map_w * TILEWIDTH
    mapSurfHeight = map_h * TILEHEIGHT

    left_blank = (WINWIDTH - mapSurfWidth)/2

    G_topleft = left_blank, 60
    G_bottomleft = left_blank, 60 + 44 * TILEHEIGHT
    G_topright = left_blank + 8 * TILEWIDTH, 60
    G_top2right = left_blank + 8 * TILEWIDTH, 60 + 4 * TILEHEIGHT
    H_topleft = left_blank + 28 * TILEWIDTH, 60 + 4 * TILEHEIGHT
    H_topright = left_blank + 58 * TILEWIDTH, 60 + 4 * TILEHEIGHT
    H_bottomleft = left_blank + 28 * TILEWIDTH, 60 + 44 * TILEHEIGHT
    H_bottomright = left_blank + 58 * TILEWIDTH, 60 + 44 * TILEHEIGHT
    I_topright = left_blank + 123 * TILEWIDTH, 60 + 4 * TILEHEIGHT
    I_bottomright = left_blank + 88 * TILEWIDTH, 60 + 44 * TILEHEIGHT
    D_topleft = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    D_topright = left_blank + 177 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    D_bottomleft = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10
    D_bottomright = left_blank + 177 * TILEWIDTH, WINHEIGHT - 10
    F_topleft = left_blank + 207 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    F_topright = left_blank + 237 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    F_bottomleft = left_blank + 207 * TILEWIDTH, WINHEIGHT - 10
    F_bottomright = left_blank + 237 * TILEWIDTH, WINHEIGHT - 10

    pygame.draw.line(DISPLAYSURF, BLUE, G_topleft, G_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, G_topleft, G_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, G_topright, G_top2right)
    pygame.draw.line(DISPLAYSURF, BLUE, G_top2right, I_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, H_topleft, H_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, H_topright, H_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, G_bottomleft, I_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, C_topleft, C_bottomleft)
    # pygame.draw.line(DISPLAYSURF, BLUE, C_bottomleft, C_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, C_topright, C_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, D_topleft, C_topright)
    # pygame.draw.line(DISPLAYSURF, BLUE, D_topleft, F_topright)
    # pygame.draw.line(DISPLAYSURF, BLUE, D_topright, D_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, D_bottomleft, F_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, F_topleft, F_bottomleft)
    # pygame.draw.line(DISPLAYSURF, BLUE, F_bottomleft, F_bottomright)
    # pygame.draw.line(DISPLAYSURF, BLUE, F_topright, F_bottomright)

def draw_border_3FM(mapObj):
    # draw the border of zones onto the DISPLAYSURF
    map_h = len(mapObj)
    map_w = len(mapObj[0])

    mapSurfWidth = map_w * TILEWIDTH
    mapSurfHeight = map_h * TILEHEIGHT

    left_blank = (WINWIDTH - mapSurfWidth)/2

    A_topleft = left_blank, WINHEIGHT - 10 - 45 * TILEHEIGHT
    A_bottomleft = left_blank, WINHEIGHT - 10
    AR_topleft = left_blank + 11 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    AR_topright = left_blank + 51 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    AR_bottomleft = left_blank + 11 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    AR_bottomright = left_blank + 51 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    B_topleft = left_blank + 22 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    B_topright = left_blank + 93 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    B_bottomleft = left_blank + 22 * TILEWIDTH, WINHEIGHT - 10
    B_bottomright = left_blank + 93 * TILEWIDTH, WINHEIGHT - 10
    C_topleft = left_blank + 93 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    C_topright = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10 - 36 * TILEHEIGHT
    C_bottomleft = left_blank + 93 * TILEWIDTH, WINHEIGHT - 10
    C_bottomright = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10
    D_topleft = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    D_topright = left_blank + 177 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    D_bottomleft = left_blank + 150 * TILEWIDTH, WINHEIGHT - 10
    D_bottomright = left_blank + 177 * TILEWIDTH, WINHEIGHT - 10
    F_topleft = left_blank + 207 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    F_topright = left_blank + 237 * TILEWIDTH, WINHEIGHT - 10 - 45 * TILEHEIGHT
    F_bottomleft = left_blank + 207 * TILEWIDTH, WINHEIGHT - 10
    F_bottomright = left_blank + 237 * TILEWIDTH, WINHEIGHT - 10

    pygame.draw.line(DISPLAYSURF, BLUE, A_topleft, AR_topleft)
    pygame.draw.line(DISPLAYSURF, BLUE, A_topleft, A_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, A_bottomleft, B_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, AR_topleft, AR_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, AR_topleft, AR_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, AR_bottomleft, B_topleft)
    pygame.draw.line(DISPLAYSURF, BLUE, AR_topright, AR_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, B_topleft, B_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, B_topleft, B_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, B_bottomleft, B_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, C_topleft, C_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, C_topleft, C_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, C_bottomleft, C_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, C_topright, C_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, D_topleft, C_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, D_topleft, F_topright)
    pygame.draw.line(DISPLAYSURF, BLUE, D_topright, D_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, D_bottomleft, F_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, F_topleft, F_bottomleft)
    pygame.draw.line(DISPLAYSURF, BLUE, F_bottomleft, F_bottomright)
    pygame.draw.line(DISPLAYSURF, BLUE, F_topright, F_bottomright)

def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()