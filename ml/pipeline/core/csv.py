
import numpy as np
import os.path

class CSVHelper:
    def __init__(self) -> None:
        pass

    def saveDictionary(self, dictionary, filename):
        np.save(filename, dictionary)

    def loadDictionary(self, filename):
        if os.path.isfile(filename):
            data = np.load(filename, allow_pickle='TRUE').item()
            return data
        return None

    def saveArrayToCSV(self, array, filename):
        np.savetxt(filename, array, delimiter=",")
    
    def csvToArray(self, filename):
        if os.path.isfile(filename):
            data = np.genfromtxt(filename, delimiter=',')
            return data
        return None