import numpy as np
import sys
import os
massConversionFactor=1.000000000000000000/6.02213670000e23/9.10938970000e-28#1822.88839 
global Water
Water={'H2O', 'water', 'HOH', 'h2o'}
global WaterDimer
WaterDimer = {'water dimer', 'H4O2'}
global ProtonatedWaterDimer
ProtonatedWaterDimer = {'H5O2+','HHOHOHH','H5O2+','h5o2plus','h5o2'}
global DeprotonatedWaterDimer
DeprotonatedWaterDimer = {'HOHOH','H3O2-', 'h3o2-', 'h3o2', 'H3O2'}
ProtonatedWaterTrimer = {'H7O3+','O3H7+', 'H7O3plus','H7O3', 'O3H7'}
ProtonatedWaterTetramer = {'H9O4+','O4H9+', 'H9O4plus','H9O4', 'O4H9'}


class molecule:
    def __init__(self,moleculeName):
        self.name=moleculeName
        if self.name in DeprotonatedWaterDimer:
            self.nAtoms=5
        self.pathDict=self.loadDict("paths.dict")
        self.potential=self.getPES()

    def getPES(self):
        sys.path.insert(0,self.pathDict["potentialPath"+self.name])
        import pes
        if self.name in DeprotonatedWaterDimer:
            pes.prepot()
            potential=pes.getpot
            print 'potential retreived for HOHOH. Be sure to feed one walker in at a time!'
        return potential

    def loadDict(self,fileName):
        fileIn=open(fileName,'r')
        pathDict={}
        for line in fileIn:
            [key,element]=line.split()
            pathDict[key]=element
        return pathDict
    
    def V(self,x):
        v=np.array([self.potential(cart_in) for cart_in in x])
        return v



    def getInitialCoordinates(self):
        #looks up the path of the coordinates for the starting positions of the walkers and makes nWalkers copies of them and then returns that as an self.nWalkers,self.nAtoms, 3 dimensional array                      
        print 'there are ', self.nAtoms , 'atoms in ', self.name
        if self.name in DeprotonatedWaterDimer:
            coords=np.array([
                    [   0.000000000000000 ,  0.000000000000000 ,  0.000000000000000 ],
                    [  -2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                    [  -2.749724314110769 ,  1.765018349357672 ,  0.000000000000000],
                    [   2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                    [   2.749724314110769 ,  1.765018349357672 ,  0.000000000000000]
                    ])
        else:
            print 'not implemented!!'
        return coords

    def get_mass(self):
        mass=np.zeros((self.nAtoms))
        massH=1.00782503223
        massO=15.99491561957
        if self.name in DeprotonatedWaterDimer:
            mass=np.array([massH,massO,massH,massO,massH])
        return mass*massConversionFactor

    def calcReducedmass(self,x):
        # for the shared proton stretch, page 42 in notebook #2                                                                   
        if self.name in ProtonatedWaterDimer and self.state==1 and self.nodeCoord=='SharedProton':
            ##COMwat1=1.0/massWater*(massO*x[:,0,:]+massH*(x[:,3,:]+x[:,4,:]))
            ##COMwat2=1.0/massWater*(massO*x[:,1,:]+massH*(x[:,5,:]+x[:,6,:]))
            ##U=x[:,2,:]-COMwat1                                              
            ##V=x[:,2,:]-COMwat2                                                                                                  
            U=x[:,2,:]-x[:,1,:]
            V=x[:,2,:]-x[:,0,:]

            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            massOamu=massO*conversionFactor
            massHamu=massH*conversionFactor
            costheta= np.diag(np.dot(U,V.T))/(magU*magV)
            #mass=1.0/(2.0*((1.0/(massOamu+massHamu+massHamu))+((1-costheta)/(massHamu))))                                        
            #corresponds to calcrncom                                                                                             

            mass=1.0/(2.0*((1.0/(massOamu))+((1-costheta)/(massHamu))))

            #Mass of water or Mass of O??                                                                                         
        elif self.name in ProtonatedWaterDimer and self.state==1 and self.nodeCoord=='StretchAntiIn':

            U=x[:,0,:]-x[:,3,:]
            V=x[:,0,:]-x[:,4,:]

            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            costhetaWat1= np.diag(np.dot(U,V.T))/(magU*magV)

            U=x[:,1,:]-x[:,5,:]
            V=x[:,1,:]-x[:,6,:]
            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            costhetaWat2= np.diag(np.dot(U,V.T))/(magU*magV)

            massOamu=massO*conversionFactor
            massHamu=massH*conversionFactor
            g=( (1.0/massOamu)+(1.0/massHamu) )  +  1.0/2.0*((costhetaWat1/massOamu)+(costhetaWat2/massOamu))

            mass= 1.0/g

        elif self.name in DeprotonatedWaterDimer and self.state==1:

            U=x[:,0,:]-x[:,1,:]
            V=x[:,0,:]-x[:,2,:]

            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            massOamu=massO*conversionFactor
            massHamu=massH*conversionFactor
            costheta= np.diag(np.dot(U,V.T))/(magU*magV)
            mass=1.0/(2.0*((1.0/(massOamu))+((1-costheta)/(massHamu))))

        elif self.name in ProtonatedWaterDimer and self.state==0:
            m2=2*(massO)*conversionFactor
            m1=massH*conversionFactor
            mass=m1*m2/(m1+m2)
            print 'why are you calculateing the reduced mass on the ground state?'  , end
        elif self.name in DeprotonatedWaterDimer and self.state==0:
            m2=2*(massO)*conversionFactor
            m1=massH*conversionFactor
            mass=m1*m2/(m1+m2)
            print 'why are you calculateing the reduced mass on the ground state?'  , end

        else:
            print 'not implemented for ', self.name , 'and', self.state, 'and', self.nodeCoord,end

        return mass

    def calcRn(self,x):
        if self.molecule in ProtonatedWaterDimer:
            if self.nodeCoord=='SharedProton':
                r1=self.bondlength(x,atom1=2, atom2=1)
                r2=self.bondlength(x,atom1=2, atom2=0)
                return r2-r1

            elif self.nodeCoord=='StretchAntiIn':
                r1=self.bondlength(x,atom1=0, atom2=3)
                r2=self.bondlength(x,atom1=0, atom2=4)
                r3=self.bondlength(x,atom1=1, atom2=5)
                r4=self.bondlength(x,atom1=1, atom2=6)
                return 0.5*(r1+r2-r3-r4)

        elif self.molecule in DeprotonatedWaterDimer:
            if self.nodeCoord=='SharedProton':
                r1=self.bondlength(x,atom1=0, atom2=1)
                r2=self.bondlength(x,atom1=0, atom2=3)#ha                                                                         
                return r2-r1

    def bondlength(self,pos,atom1=1,atom2=2):
        length=(pos[:,atom1,0]-pos[:,atom2,0])**2+(pos[:,atom1,1]-pos[:,atom2,1])**2+(pos[:,atom1,2]-pos[:,atom2,2])**2
        length=np.sqrt(length)
        return length

    def mag(self,xList):
        magnitude=np.zeros(xList.shape[0])
        for i,x in enumerate(xList):
            magnitude[i]=np.sqrt(x[0]*x[0]+x[1]*x[1]+x[2]*x[2])
        return magnitude
