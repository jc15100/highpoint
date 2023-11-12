
import numpy as np

class CSVHelper:
    def __init__(self) -> None:
        pass

    def saveArrayToCSV(self, array, filename):
        np.savetxt(filename, array, delimiter=",")
    