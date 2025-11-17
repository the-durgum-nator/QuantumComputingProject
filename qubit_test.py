from qubit import Qubit
import numpy as np

q0 = Qubit(0,1)
#q0 = Qubit(1/np.sqrt(2),1/np.sqrt(2))
print(q0)

q0.rz(np.pi)
print(q0)

#print(Qubit.spherical_to_amp(3.14,0))