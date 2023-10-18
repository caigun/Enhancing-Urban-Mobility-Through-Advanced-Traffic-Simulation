import pandas as pd
import matplotlib.pyplot as plt
import re
import util

class lightNode():
    def __init__(self, latitude, longitude, streets=[], successors=[]):
        self.latitude=latitude
        self.longitude=longitude
        self.streets=streets
        self.successors=successors

class RoadMap():
    def __init__(self,df):
        self.df=df.loc[:,("STREET1","STREET2","STREET3","shape")]
        self.lightNumber=len(df["STREET1"])
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

    def drawLights(self, highLight=None):
        f = plt.figure() 
        f.set_figwidth(10) 
        f.set_figheight(6) 
        plt.scatter(self.df["dtx"], self.df["dty"], s=5)
        if highLight:
            x=[]
            y=[]
            for i in roads.roads[highLight]:
                y.append(i.latitude)
                x.append(i.longitude)
            plt.scatter(x,y,s=5,color='red')
        plt.show()

    def _reconstructNodes(self):
        """
        To find out every node(traffic light)'s successors(the next traffic lights for drivers who passes this node)
        according to the street/road information stored in self.df, and link the closest node of the same street/road
        to be the next node.

        Every nodes have these information:

        node.streets = array containing all streets/roads the node in

        node.successors = array containing all the neiboring nodes that are accessible from the current node

        node.latitude = latitude of this node, i.e., df["dty"]
        
        node.longitude =  longitude of this node, i.e., df["dtx"]
        """
        self.nodes=[]
        self.roads=util.Counter()
        for index, row in self.df.iterrows():
            node=lightNode(row["dty"],row["dtx"])
            for i in [row["STREET1"],row["STREET2"],row["STREET3"]]:
                if i:
                    node.streets.append(i)
                    rd=self.roads[i]
                    if rd==0:self.roads[i]=[node]
                    else:self.roads[i].append(node)
        pass
    
    def _reconstructRoads(self):
        """
        Acoording to the nodes constructed with successors, link all the nodes with their successor(which is a street/road
        segment).
        (INTENDED) Store the road data in terms of dictionary: key=(node1, node2), value=length of this road
        """
        pass

    def drawRoads(self):
        pass

    def drawRoadsWithStress(self, stress):
        pass

if __name__ == '__main__':
    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df)
    roads.drawLights("19TH AVE")
    plt.show()