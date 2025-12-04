import numpy as np
from cmath import phase
import random

class Qubit:
    '''
    '''
    BASE_0 = np.array([1,0])
    BASE_1 = np.array([0,1])
    
    def __init__(self,amp_a=1+0j,amp_b=0+0j):
        squared_sum = abs(amp_a)**2 + abs(amp_b)**2
        assert np.isclose(squared_sum,1), f"Qubit's squared amplitudes must add up to 1, not {squared_sum}"
        #amplitudes 
        self.amp_a = amp_a + 0j #cos(theta/2)
        self.amp_b = amp_b + 0j#e^(i*phi) * sin(theta/2)
        
        #phase angles in rads, spherical cooridates 
        # 0 <= theta <= pi, angle between vertical axis z and toward horizontal xy plane
        # 0 <= phi <= 2pi, angle from x to y axis
        self.theta,self.phi = Qubit.amp_to_spherical(amp_a,amp_b)
        
        #cartesian coordinates 
        self.coords =  Qubit.spherical_to_cartesian(self.theta,self.phi)# x, y, z 
        
        self.is_collapsed = False
        
        
    #GATE OPERATIONS    
    def __update(self):
        #bloch angle rotation method
        angles = Qubit.amp_to_spherical(self.amp_a,self.amp_b)
        self.theta = angles[0]
        self.phi = angles[1]
        
        #update coords
        self.coords = Qubit.amp_to_cartesian(self.amp_a,self.amp_a)
        
        
    def rx(self,angle,clockwise = True): #rotate x by angle
        
        #bloch angle rotation method
        #self.theta = np.pi - self.theta
        #self.phi = -self.phi
        
        #matrix multiplication method
        #matrix = np.array([[np.cos(angle/2)+0j,-1j*np.sin(angle/2)],[-1j*np.sin(angle/2),np.cos(angle/2)+0j]])
        #vector = self.state_vector()
        #result = matrix @ vector
        #self.amp_a = result[0]
        #self.amp_b = result[1] 
        self.__update()
        return self.coords 
    
    def ry(self,angle,clockwise = True): #rotate Y by angle
        # theta' = pi - theta
        # phi' = pi -phi
        #bloch angle rotation method
        #self.theta = np.pi - self.theta
        #self.phi = np.pi - self.phi
        
        #matrix multiplication method
        if(not self.is_collapsed):
            matrix = np.array([[np.cos(angle/2)+0j,-np.sin(angle/2)+0j],[np.sin(angle/2)+0j,np.cos(angle/2)+0j]])
            vector = self.state_vector()
            result = matrix @ vector
            self.amp_a = result[0]
            self.amp_b = result[1] 
        
        self.__update()
        return self.coords
       
    
    def rz(self,angle,clockwise = True):  #rotate Z by angle
        if(not self.is_collapsed):
            #bloch angle rotation method
            self.phi = angle + self.phi
            
            #matrix multiplication method
            matrix = np.array([[1,0],[0,-1]])
            vector = self.state_vector()
            result = matrix @ vector
            self.amp_a = result[0]
            self.amp_b = result[1] 
        
        self.__update()
        return self.coords 
    
    def x(self):  #rotate 180 around x-axis, theta' = pi - theta, phi' = -phi
        
        if(not self.is_collapsed):
            #bloch angle rotation method
            self.theta = np.pi - self.theta
            self.phi = -self.phi
            
            #matrix multiplication method
            matrix = np.array([[1,0],[0,1]])
            vector = self.state_vector()
            result = matrix @ vector
            self.amp_a = result[0]
            self.amp_b = result[1] 
        
        self.__update()
        return self.coords  

        
    def y(self):
    #Y Gate - rotate 180 around y
       pass    
    
    def z(self): #Z Gate - rotate 180 around z, theta' = theta, phi' = pi + phi
        return self.rz(np.pi)
    
    
    def h(self):
        if(not self.is_collapsed):
            #matrix multiplication method
            matrix = 1/np.sqrt(2) * np.array([[1,1],[1,-1]])
            vector = self.state_vector()
            result = matrix @ vector
            self.amp_a = result[0]
            self.amp_b = result[1] 
        
        self.__update()
        return self.coords 
    
    def p(self, angle):
        if(not self.is_collapsed):
            matrix = np.array[[1,0][0,np.exp(1j*angle)]]
            vector = self.state_vector()
            
            result = matrix @ vector
            self.amp_a = result[0]
            self.amp_b = result[1] 
        self.__update()
        return self.coords 
    
    def s(self):
        return self.p(np.pi)
    
    def t(self):
        return self.p(np.pi/2)
    
    def measure(self): #collapses qubit state to either |0> or |1> based on ampltiude
        
        if(not self.is_collapsed):
            prob_0 = abs(self.amp_a)**2
            if(random.random()<=prob_0):
                self.amp_a = 1
                self.amp_b = 0
                self.theta = 0
                self.phi = 0
                self.coords = (0,0,1)
            else:
                self.amp_a = 0
                self.amp_b = 1
                self.theta = np.pi
                self.phi = 0
                self.coords = (0,0,-1)
            self.is_collapsed = True
        self.__update()
        return self.coords
    
    # PRINTING AND REPRESENTATIONS
    
    def __str__(self):
        #\nBra-Ket: {f"({self.amp_a.real:.0f}+{self.amp_a.imag:.0f}j)"}|0> + {f"({self.amp_b.real:.0f}+{self.amp_b.imag:.0f}j)"}|1>\n
        return f"Qubit Representations:\nState Vector: {self.state_vector()}\nBloch Angles: θ = {f"{round(self.theta,5):.3g}"} φ = {f"{round(self.phi,5):.3g}\nCartesian Coords: ({round(self.coords[0],3)}, {round(self.coords[1],3)}, {round(self.coords[2],3)})\n"}"
    
    def state_vector(self): 
        return self.amp_a * self.BASE_0 + self.amp_b * self.BASE_1 
     
    def spherical_angles(self):
        return (self.theta,self.phi)
    
    def spherical_to_amp(theta,phi):
        amp_a = np.cos(theta/2) 
        amp_b = np.exp(1j*phi) *np.sin(theta/2) #e^(i*phi) * sin(theta/2)
        return (amp_a,amp_b)
    
    def spherical_to_cartesian(theta,phi):
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(phi) * np.cos(theta)
        z = np.cos(theta)
        return (x,y,z)
    
    def amp_to_spherical(amp_a,amp_b): # phi not correct, has issues when theta is 0 and amp_a = 1
        theta = (2*np.arccos(amp_a)).real
        phi = phase(amp_b) - phase(amp_a) #np.log(amp_b/np.sin(theta/2))/1j
        return(theta,phi) 
    
    def amp_to_cartesian(amp_a,amp_b):
        spherical = Qubit.amp_to_spherical(amp_a,amp_b)
        return Qubit.spherical_to_cartesian(spherical[0],spherical[1])
    
    def cartesian_to_spherical(x,y,z):
        pass
    
    def cartesian_to_amp(x,y,z):
        pass
    
    