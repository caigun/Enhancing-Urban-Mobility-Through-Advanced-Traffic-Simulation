import pandas as pd
import matplotlib.pyplot as plt
import re
import util
import numpy as np
import math

class lightNode():
    def __init__(self, latitude, longitude, cnn, streets=[], successors=set()):
        self.latitude=latitude
        self.longitude=longitude
        self.streets=streets
        self.successors=successors
        self.coo=(latitude,longitude)
        self.cnn=cnn

class RoadMap():
    """
    This is the main part defining the problem.

    ** When initializing the system, there is a parameter that is avalible to choose:

    lenTol: the tolerance level of the lenth between two ligths on the same street/road\\
    when this level is set to reletively high (or even inf, as default), the system may
    create strange roads (from a very far crossroad to another), since there may be no
    other traffic lights. This situation can be solved if all the crossroads (including
    those without traffic lights, or we can imagine that the traffic lights there is always
    green). However in this simplier model, we just do not consider the non-traffic lights
    crossroads.

    ** Useful parameters that you can retrived from this class:

    * df = all traffic lights data
    * lenTol = road lenth tolerance level
    * rdSegment = road Segments (note that this is a two-way segments dictionary, refer to
    _reconstructRoads for detailed usage)
    * nodes = all nodes in this system
    
    ** Useful functions:
    
    * drawLights(highlight=None) : draw all the lights in the map, if hightLight (a specific road
    name, string) is given, the map will highlight all the lights on this street/road.

    * findNode(cnn) : return a node with certain cnn

    * drawRoads(highlight=None) : draw all the roads (segments) that were identified by the system.
    if highlight is given, this function will only draw the highlight street/road. Note: this function
    is still improving. Please report if there is any bug. :)

    * getSuccessors(node) : return all the successors that can go from this light. Stored in array

    * drawRoadsWithStress(stress) : draw all the roads with a given traffic jam stress dictionary.
    """
    def __init__(self,df,lenTol=float('inf')):
        self.df=df.loc[:,("STREET1","STREET2","STREET3","shape","CNN")]
        self.lightNumber=len(df["STREET1"])
        self.lenTol=lenTol
        self._reconstructLights()
        self._reconstructNodes()
        self._reconstructRoads()

    def _reconstructLights(self):
        lightLocation=self.df["shape"]
        pattern = r'POINT \((-?\d+\.\d+) (-?\d+\.\d+)\)'
        dtx=[]
        dty=[]
        for i in lightLocation:
            match = re.search(pattern, i)
            dtx.append(float(match.group(1)))
            dty.append(float(match.group(2)))
        self.df["dtx"]=dtx
        self.df["dty"]=dty

    def drawLights(self, highlight=None):
        plt.scatter(self.df["dtx"], self.df["dty"], s=5)
        if highlight:
            x=[]
            y=[]
            for i in self.roads[highlight]:
                y.append(i.latitude)
                x.append(i.longitude)
            plt.scatter(x,y,s=5,color='red')
        # plt.show()

    def findNode(self, cnn):
        """
        Search and return the specific node by CNN number
        """
        for i in self.nodes:
            if i.cnn==cnn: return i

    def _reconstructNodes(self):
        """
        To find out every node(traffic light)'s successors(the next traffic lights for drivers who passes this node)
        according to the street/road information stored in self.df, and link the closest node of the same street/road
        to be the next node.

        Every nodes have these information:
        * node.streets = array containing all streets/roads the node in
        * node.successors = array containing all the neiboring nodes that are accessible from the current node
        * node.latitude = latitude of this node, i.e., df["dty"]
        * node.longitude = longitude of this node, i.e., df["dtx"]
        * node.coo = coordinate of this node

        The successor collecting process is done in self._reconstructRoads
        """
        self.nodes=[]
        self.roads=util.Counter()
        for index, row in self.df.iterrows():
            node=lightNode(row["dty"],row["dtx"],row["CNN"],successors=set())
            for i in [row["STREET1"],row["STREET2"],row["STREET3"]]:
                if i==i:
                    node.streets.append(i)
                    rd=self.roads[i]
                    if rd==0:self.roads[i]=[node]
                    else:self.roads[i].append(node)
            self.nodes.append(node)

    def l2Distance(self, point1, point2):
        return math.sqrt((point1[0]-point2[0])**2+(point1[1]-point2[1])**2)

    def _findClosestKPointandDistance(self, nodes:list, node:tuple):
        """
        Return the nodes that have distance to the specified node in increasing order,
        not containing the node itself
        """
        bank={}
        for i in nodes:
            bank[i]=self.l2Distance(node.coo,i.coo)
        sortedBank=sorted(bank.items(), key=lambda item: item[1])
        return [i for i in sortedBank[1:]]
    
    def _isReverseDirection(self, node, successor1, successor2):
        """
        To check whether the two closest successors are in the same direction(in this case, they are not likely
        to be both successors)
        """
        v1=(node.latitude-successor1.latitude, node.longitude-successor1.longitude)
        v2=(node.latitude-successor2.latitude, node.longitude-successor2.longitude)
        if v1[0]*v2[0]+v1[1]*v2[1]<=0:
            return True
        else:return False

    def _reconstructRoads(self):
        """
        Acoording to the nodes constructed with successors, link all the nodes with their successor(which is a street/road
        segment).

        Store the road data in terms of dictionary: key=set(node1, node2), value=road
        """
        self.rdSegment={}
        for road in self.roads.keys():
            nodes=self.roads[road]
            if len(nodes)==1:continue
            elif len(nodes)==2:
                if self.l2Distance(nodes[0].coo,nodes[1].coo)>self.lenTol:
                    continue
                nodes[0].successors.add(nodes[1])
                self.rdSegment[(nodes[1],nodes[0])]=road
                self.rdSegment[(nodes[0],nodes[1])]=road
                nodes[1].successors.add(nodes[0])
                continue
            for node in nodes:
                kPoint=self._findClosestKPointandDistance(nodes, node)
                successor1=kPoint[0][0]
                successor2=kPoint[1][0]
                if self._isReverseDirection(node, successor1, successor2):
                    if not kPoint[0][1]>self.lenTol:
                        node.successors.add(successor1)
                        self.rdSegment[(node,successor1)]=road
                        self.rdSegment[(successor1,node)]=road
                    if not kPoint[1][1]>self.lenTol:
                        node.successors.add(successor2)
                        self.rdSegment[(node,successor2)]=road
                        self.rdSegment[(successor2,node)]=road
                else:
                    if kPoint[0][1]>self.lenTol:
                        continue
                    node.successors.add(successor1)
                    self.rdSegment[(node,successor1)]=road
                    self.rdSegment[(successor1,node)]=road
                    for i in kPoint[2:]:
                        if i[1]>self.lenTol:break
                        if self._isReverseDirection(node, successor1, i[0]):
                            self.rdSegment[(node,i[0])]=road
                            self.rdSegment[(i[0],node)]=road
                            node.successors.add(i[0])
                            break

    def getSuccessors(self, node):
        return node.successors

    def drawRoads(self, highlight=None):
        if highlight!=None:
            for nodes, road in self.rdSegment.items():
                if road==highlight:
                    plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color="RED")
                else:
                    plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color=(110/256,130/256,230/256))
            return
        for nodes, rd in self.rdSegment.items():
            plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color=(110/256,130/256,230/256))

    def drawRoadsWithStress(self, stress=util.Counter()):
        colorGradient=[(51/256,255/256,51/256), (153/256,255/256,51/256), (255/256,255/256,51/256),\
                       (255/256,153/256,51/256), (51/256,255/256,51/256), (255/256,51/256,51/256)]
        for nodes, rd in self.rdSegment.items():
            plt.plot([i.longitude for i in nodes],[i.latitude for i in nodes], color=colorGradient[stress[nodes]])
        pass

if __name__ == '__main__':
    """
    For testing only
    """
    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df, 0.03)
    f = plt.figure()
    f.set_figwidth(10)
    f.set_figheight(6)
    # roads.drawRoads("VALENCIA")
    roads.drawRoadsWithStress()
    roads.drawLights("VALENCIA")
    # roads.drawRoads()
    plt.show()