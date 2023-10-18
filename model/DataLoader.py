import pandas as pd
import matplotlib.pyplot as plt
import re

class RoadMap():
    def __init__(self,df):
        self.df=df[["STREET1","STREET2","shape"]]
        self._reconstructLights()

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

    def drawLights(self):
        plt.scatter(self.df["dtx"], self.df["dty"])
        plt.show()
    
    def _reconstructRoads(self):
        pass

if __name__ == '__main__':
    df=pd.read_csv("Traffic_Signals.csv")
    roads=RoadMap(df)
    roads.drawLights()