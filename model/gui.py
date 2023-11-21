import pygame
import DataLoader
import Simulation
import time
import os

def drawRoadsWithStress(screen, model:Simulation.Simulation, stress_data, width=1,\
                        longitudeRange=(37.7,37.83), latitudeRange=(-122.52,-122.34),\
                        pixelx=1200, pixely=800):
    colorGradient=[(51,255,51), (153,255,51), (255,255,51),\
                    (255,153,51), (51,255,51), (255,51,51),\
                    (0,0,0)]
    yd=longitudeRange[1]-longitudeRange[0]
    xd=latitudeRange[1]-latitudeRange[0]
    ys=longitudeRange[0]
    xs=latitudeRange[0]
    for nodes, stress in stress_data.items():
        n1, n2 = nodes
        l1, l2 = (n1.longitude, n1.latitude), (n2.longitude, n2.latitude)
        if l1==l2:
            continue
        direction=[i*model.roads.scale for i in DataLoader.rightShift(l1,l2)]
        color=colorGradient[stress]
        x1=int((nodes[0].longitude+direction[0]-xs)/xd*pixelx)
        y1=pixely-int((nodes[0].latitude+direction[1]-ys)/yd*pixely)
        x2=int((nodes[1].longitude+direction[0]-xs)/xd*pixelx)
        y2=pixely-int((nodes[1].latitude+direction[1]-ys)/yd*pixely)
        pygame.draw.line(screen, color, (x1,y1),(x2,y2), width)

def run(model, save=True):
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))

    if save:
        save_dir="animation/"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    stress_data = model.loadStressData()
    i=0
    max_i=len(stress_data)
    myfont=pygame.font.Font(None, 60)
    black=0,0,0
    running = True
    stress=[]
    while running and i<max_i:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((224, 255, 255)) # sky-blue background

        drawRoadsWithStress(screen, model, stress_data[i])
        stress.append(sum(stress_data[i].values())/len(stress_data[i].values()))
        i+=1
        textImage=myfont.render("Time: "+str(i*model.updateTime), True, black)
        screen.blit(textImage,(10,10))
        pygame.display.flip()
        if save:
            pygame.image.save(screen, os.path.join(save_dir, f"frame_{i}.png"))

        # time.sleep(0.01)

    pygame.quit()