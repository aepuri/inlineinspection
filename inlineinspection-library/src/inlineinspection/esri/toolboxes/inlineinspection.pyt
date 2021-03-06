#import arcpy

from inlineinspection.pressurecalculator.pressurecalculator import PressureCalculator
from inlineinspection.anomalygrowthcalculator.anomalygrowthcalculator import AnomalyGrowthCalculator
from inlineinspection.anomalygrowthcalculator.anomalyconverter import AnomalyConverter
from inlineinspection.anomalygrowthcalculator.anomalycomparer import AnomalyComparer

class Toolbox(object):

    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""

        self.label = "PIMS ILI Tools"
        self.alias = "inlineinspection"

        # List of tool classes associated with this toolbox
        self.tools = [PressureCalculator, AnomalyConverter,AnomalyComparer,AnomalyGrowthCalculator   
                      ]
