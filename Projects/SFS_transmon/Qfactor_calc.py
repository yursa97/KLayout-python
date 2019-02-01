#%%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from resonator_tools import circuit
from IPython.display import display

#%%
table = pd.read_csv(r"C:\Users\andre\Documents\chip_designs\chip_design_good_5_400_7GHz.csv",
    header=None, skiprows=2, names=["Frequency (GHz)","RE[S11]","IM[S11]","RE[S12]","IM[S12]","RE[S21]","IM[S21]","RE[S22]","IM[S22]"],
    delimiter=" ")
table.head()

#%%
port = circuit.notch_port(table["Frequency (GHz)"], table["RE[S21]"] + 1j * table["IM[S21]"])
port.autofit()
port.plotall()

#%%
display(pd.DataFrame([port.fitresults]).applymap(lambda x: "{0:.2e}".format(x)))

#%%
port.fitresults['fr']

#%%
