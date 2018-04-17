import numpy as np
import sys
import os
global massH
global massO
global massD
massH=1.00782503223
massD=2.0141017778
massO=15.99491561957
massConversionFactor=1.000000000000000000/6.02213670000e23/9.10938970000e-28#1822.88839 
ang2bohr=1.88973
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
IsotopeKeywords = {'notDeuterated','DeuteratedTwice','fullyDeuterated'}

class molecule:
    def __init__(self,moleculeName):
        self.name=moleculeName
        if self.name in DeprotonatedWaterDimer:
            self.nAtoms=5
            self.names=['H','O','H','O','H']
        self.pathDict=self.loadDict("paths.dict")
        self.potential=self.getPES()
        self.surfaceName="GroundState"
        self.dipole=self.getDIPOLE()
        self.isotope='notDeuterated'
    def set_isotope(self,keyword):
        print 'resetting isotope to ', keyword
        if keyword in IsotopeKeywords:
            self.isotope=keyword
            if self.isotope=='DeuteratedTwice':
                self.names=['H','O','D','O','D']
            elif self.isotope=='fullyDeuterated':
                self.names=['D','O','D','O','D']
            elif self.isotope=='notDeuterated':
                self.names=['H','O','H','O','H']
            print 'atoms are now', self.names
    def setNodalSurface(self,surfaceName,side):
        self.surfaceName=surfaceName
        self.side=side
        self.state=1
    def getPES(self):
        sys.path.insert(0,self.pathDict["potentialPath"+self.name])
        import pes
        if self.name in DeprotonatedWaterDimer:
            pes.prepot()
            potential=pes.getpot
            print 'potential retrieved for HOHOH. Be sure to feed one walker in at a time!'
        return potential

    def getDIPOLE(self):
        sys.path.insert(0,self.pathDict["dipolePath"+self.name])
        import h3o2dms2 as dms
        if self.name in DeprotonatedWaterDimer:
            dms.predip()
            dip=dms.mycalcdip
        #since all dipole moment calculations need eckart rotation...loading the reference coordinates
        self.refPos=self.loadRefCoord()
        return dip
            
    def loadDict(self,fileName):
        fileIn=open(fileName,'r')
        pathDict={}
        for line in fileIn:
            [key,element]=line.split()
            pathDict[key]=element
        return pathDict
    def loadRefCoord(self):
        if self.name in DeprotonatedWaterDimer:
            coordsMin=np.array([[ 0.2981678882048853 ,   -2.4557992072743176E-002,  -5.5485232545510215E-002],
                             [ -2.354423404994569 ,     0.000000000000000     ,    0.000000000000000],
                             [ -2.858918674095194 ,     1.111268022307282     ,   -1.352651141853729],
                             [  2.354423404994569 ,     0.000000000000000     ,    0.000000000000000],
                             [  2.671741580470489 ,     1.136107563104921     ,    1.382886181959795]])

        return coordsMin

    def V(self,x):
        #print 'v',self.surfaceName,self.side,
        v=np.array([self.potential(cart_in) for cart_in in x])
        if self.surfaceName=='SharedProton':
            
            if self.side=='Right':
                r=self.calcRn(x)
                v[(r<0)]=1000.00
            elif self.side=='Left':
                r=self.calcRn(x)
                v[(r>0)]=1000.00
            else:
                donothing=1
        elif self.surfaceName=='OHStretchAnti':
            #if self.side=='Both':
            #    r,swap=self.calcStretchAnti(x)
            #    if (len(swap)>0):
            #        print 'swap list', swap, 'v before',v[swap],
            #        v[np.array(swap)]=1000.00
            #        print 'v after', v[swap]
            if self.side=='Right':      
                #swap=self.sortProtons()
                r=self.calcStretchAnti(x)
                v[(r<0)]=1000.00
            elif self.side=='Left':
                #swap=self.sortProtons()
                r=self.calcStretchAnti(x)
                v[(r>0)]=1000.00
            else:
                donothing=1
        return v

    def calcDipole(self,x):
        eckRotx=self.eckartRotate(x)
        dipoleVectors=self.dipole(eckRotx)
        
        return dipoleVectors


    def eckartRotate(self,pos,specialCond=False):
        if len(pos.shape)<3:
            pos=np.array([pos])
        nMolecules=pos.shape[0]
        Fvec=np.zeros((3,3))
        Fvec2=np.zeros((3,3))
        newCoord=np.zeros(pos.shape)
        rHC=np.zeros((nMolecules,3))
        rHCprime=np.zeros((nMolecules,3))
    
        #Center of Mass     
        mass=self.get_mass()
        com=np.dot(mass,pos)/np.sum(mass)
        rs=0.000
        rsprime=0.000

        #First Translate:                                                                                     
        ShiftedMolecules=pos-com[:,np.newaxis,:]

        #Equation 3.1                                                                                         
        for moli,molecule in enumerate(ShiftedMolecules):
            Fvec=np.zeros((3,3))
            for atom,massa,eckatom in zip(molecule,mass,self.refPos):
                Fvec=Fvec+massa*np.outer(eckatom,atom)
            #F from eqn 3.4b                                                                                  
            FF=np.dot(Fvec,Fvec.transpose())
            #Diagonalize FF                                                                                   
            sortEigValsF,sortEigVecF=np.linalg.eigh(FF)
            sortEigVecFT=-sortEigVecF.transpose()
            if specialCond:
                print 'special condition activated!'
                print 'eigenvals \n',sortEigValsF
                print 'vect \n',sortEigVecFT
            if len(np.where(sortEigValsF<=0)[0])!=0:
                #sortEigVecFT=np.abs(sortEigVecFT)                                                            
                sortEigValsF=np.abs(sortEigValsF)
                invRootDiagF=sortEigValsF
                for e,element in enumerate(sortEigValsF):
                    if element>0:
                        invRootDiagF[e]=1.0/np.sqrt(element)
            #Get the inverse sqrt of diagonalized(FF)                                                         
            else:
                invRootDiagF=1.0/np.sqrt(sortEigValsF)
            # F^{-1/2}                                                                                         
            invRootF=np.dot(invRootDiagF[np.newaxis,:]*-sortEigVecF,sortEigVecFT)
            eckVecs=np.dot(Fvec.transpose(),invRootF)
            newCoord[moli]= np.dot(molecule,eckVecs)

            if len(np.where(np.isnan(newCoord[moli]))[0])!=0:
                print 'whaaaaaT?! nan',np.where(np.isnan(newCoord[moli])),'\ncoords:\n',newCoord[moli]
                print '   molecule number:',moli,'\n   sortEigValsF: \n', sortEigValsF,'\n   molecule: \n', molecule, 
                print '\n   eckVecs \n', eckVecs
                octopus

        return newCoord


    def getInitialCoordinates(self):
        #looks up the path of the coordinates for the starting positions of the walkers and makes nWalkers copies of them and then returns that as an self.nWalkers,self.nAtoms, 3 dimensional array                      
        print 'there are ', self.nAtoms , 'atoms in ', self.name
        if self.name in DeprotonatedWaterDimer:
            coordsMin=np.array([ [   0.000000000000000 ,  0.000000000000000 ,  0.000000000000000],
                              [  2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                              [  2.749724314110769 ,  -1.765018349357672 ,  0.000000000000000],
                              [   -2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                              [   -2.749724314110769 ,  -1.765018349357672 ,  0.000000000000000]
                              ])
            coordsMinRotated=np.array([[0.0000000,   0.000000000000000 ,  0.000000000000000  ],
                             [0.0000000,  2.306185590098382 ,  0.000000000000000   ],
                             [0.0000000,  2.749724314110769 ,  -1.765018349357672  ],
                             [0.0000000,   -2.306185590098382 ,  0.000000000000000 ],
                             [0.0000000,   -2.749724314110769 ,  -1.765018349357672]
                             ])
            
            coordsc2v=np.array([ [   0.000000000000000 ,  0.000000000000000 ,  0.000000000000000],
                                 [  -2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                                 [  -2.749724314110769 ,  1.765018349357672 ,  0.000000000000000],
                                 [   2.306185590098382 ,  0.000000000000000 ,  0.000000000000000],
                                 [   2.749724314110769 ,  1.765018349357672 ,  0.000000000000000]])
            coordsc2h=np.array([ [   0.000000000000000 ,   0.000000000000000       ,  0.000000000000000],
                                 [  -2.304566686034061 ,   0.000000000000000       ,  0.000000000000000],
                                 [  -2.740400260927908 ,   1.0814221449986587E-016 ,  -1.766154718409233],
                                 [   2.304566686034061 ,   0.000000000000000       ,  0.000000000000000],
                                 [  2.740400260927908  ,   1.0814221449986587E-016 ,  1.766154718409233]])
            coordsSaddle=np.array([[ 0.000000000000000   , 0.000000000000000 ,  0.000000000000000 ],   
                                    [ -2.303263755760085 , 0.000000000000000 ,  0.000000000000000 ],  
                                    [ -2.720583162407882 , 1.129745554266140 ,  -1.363735721982301],  
                                    [ 2.303263755760085  , 0.000000000000000 ,  0.000000000000000 ],   
                                    [ 2.720583162407882  , 1.129745554266140 ,  1.363735721982301 ]])

            coordsAsymStart=np.array([[ 0.2981678882048853 ,   -2.4557992072743176E-002,  -5.5485232545510215E-002],
                                      [ -2.354423404994569 ,     0.000000000000000     ,    0.000000000000000],
                                      [ -2.858918674095194 ,     1.111268022307282     ,   -1.352651141853729],
                                      [  2.354423404994569 ,     0.000000000000000     ,    0.000000000000000],
                                      [  2.771741580470489 ,     1.236107563104921     ,    1.482886181959795]])

            

            coordsAsymStart2=np.array([[   3.52234 ,    1.01649  ,    1.28596],
                                      [   2.35442 ,    0.00000  ,    0.00000],
                                      [   0.29817 ,   -0.02456  ,   -0.05549],
                                      [  -2.35442 ,    0.00000  ,    0.00000],
                                       [  -2.85892 ,    1.11127  ,   -1.35265]])



            coords=coordsAsymStart
            
            
#            coords=np.array([[ 0.26591125,  0.07072797, -0.02256279],
#WW         WW                [ 0.55610034,  2.83109547,  0.14883552],
#  W       W                  [ 1.50122114,  1.22631416, -0.59092507],
#   W  W  W                   [-0.11962985, -1.87021212,  0.22794889],
#    W   W                    [ 1.20503929, -0.77837156,  0.71051114]])
            
        
        else:
            print 'not implemented!!'
        return coords
    def getMassSharedProton(self):
        if self.isotope=='DeuteratedTwice':
            return massH
        if self.isotope=='notDeuterated':
            return massH
        if self.isotope=='fullyDeuterated':
            return massD
    def getMassOuterProton(self):
        if self.isotope=='DeuteratedTwice':
            return massD
        if self.isotope=='notDeuterated':
            return massH
        if self.isotope=='fullyDeuterated':
            return massD

    
    def get_mass(self):
        mass=np.zeros((self.nAtoms))
        if self.name in DeprotonatedWaterDimer:
            mass=np.array([massH,massO,massH,massO,massH])
            if self.isotope=='DeuteratedTwice':
                mass[2]=massD
                mass[4]=massD
            if self.isotope=='fullyDeuterated':
                mass[2]=massD
                mass[4]=massD
                mass[0]=massD
            
        return mass*massConversionFactor

    def calcReducedmass(self,x):
        # for the shared proton stretch, page 42 in notebook #2
        massOamu=massO*massConversionFactor

        if self.name in ProtonatedWaterDimer and self.state==1 and self.surfaceName=='SharedProton':
            ##COMwat1=1.0/massWater*(massO*x[:,0,:]+massH*(x[:,3,:]+x[:,4,:]))
            ##COMwat2=1.0/massWater*(massO*x[:,1,:]+massH*(x[:,5,:]+x[:,6,:]))
            ##U=x[:,2,:]-COMwat1                                              
            ##V=x[:,2,:]-COMwat2                                       

            U=x[:,2,:]-x[:,1,:]
            V=x[:,2,:]-x[:,0,:]
            massHamu=self.getMassSharedProton()*massConversionFactor
            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            
            costheta= np.diag(np.dot(U,V.T))/(magU*magV)
            #mass=1.0/(2.0*((1.0/(massOamu+massHamu+massHamu))+((1-costheta)/(massHamu))))                                        
            #corresponds to calcrncom                                                                                             

            mass=1.0/(2.0*((1.0/(massOamu))+((1-costheta)/(massHamu))))
            #print 'average mass', np.average(mass)
            #Mass of water or Mass of O??                                                                                         
        elif self.name in ProtonatedWaterDimer and self.state==1 and self.surfaceName=='StretchAntiIn':

            massHamu=self.getMassOuterProton()*massConversionFactor

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

            g=( (1.0/massOamu)+(1.0/massHamu) )  +  1.0/2.0*((costhetaWat1/massOamu)+(costhetaWat2/massOamu))

            mass= 1.0/g

        elif self.name in DeprotonatedWaterDimer and self.surfaceName=='SharedProton' and self.state==1:
            massHamu=self.getMassSharedProton()*massConversionFactor
            U=x[:,1,:]-x[:,0,:]
            V=x[:,3,:]-x[:,0,:]
            magU=np.sqrt(U[:,0]**2+U[:,1]**2+U[:,2]**2)
            magV=np.sqrt(V[:,0]**2+V[:,1]**2+V[:,2]**2)
            costheta= np.diag(np.dot(U,V.T))/(magU*magV)
            mass=1.0/(2.0*((1.0/(massOamu))+((1.000000-costheta)/(massHamu))))
            #print 'average mass', np.average(mass)

        elif self.name in DeprotonatedWaterDimer and self.surfaceName=='Z-displacement' and self.state==1:
            massHamu=self.getMassSharedProton()*massConversionFactor
            mass=1.0/((1.0/massHamu)+(1.0/(2.0*massOamu)))
            
        elif  self.name in DeprotonatedWaterDimer and self.surfaceName=='LocalOHStretch' and self.state==1:
            massHamu=self.getMassOuterProton()*massConversionFactor
            mass=(massHamu*massOamu)/(massHamu+massOamu)

        elif self.name in DeprotonatedWaterDimer and self.surfaceName=='OHStretchAnti' and self.state==1:
            massHamu=self.getMassOuterProton()*massConversionFactor
            g=(1.0/massHamu)+ (1.0/massOamu)
            mass=1.0/g #(massHamu*massOamu)/(massHamu+massOamu)
            #print 'average mass', np.average(mass)
        elif self.name in ProtonatedWaterDimer and self.state==0:
            m1=self.getMassOuterProton()*massConversionFactor
            m2=2*(massO)*conversionFactor
            #m1=massH*conversionFactor
            mass=m1*m2/(m1+m2)
            print 'why are you calculating the reduced mass on the ground state?'  , end
        elif self.name in DeprotonatedWaterDimer and self.state==0:
            m2=2*(massO)*conversionFactor
            m1=self.getMassOuterProton()*massConversionFactor
            mass=m1*m2/(m1+m2)
            print 'why are you calculating the reduced mass on the ground state?'  , end

        else:
            print 'not implemented for ', self.name , 'and', self.state, 'and', self.surfaceName,end

        return mass
    
    def sortProtons(self,x):
        #Defunct!
        defunct
        #This is a fun function!  It was written to correct for the isomerization of H3O2-.  The isomerization was a problem
        #Because the anti symmetric stretch (and actually all of the internal coordinates) were defined by the atom positions 
        #in the coordinate array.  
        #Input is the coordinate array, x.  This function DOES NOT make a deep copy of the coordinate array passed in.  So the 
        #swapping that takes place CHANGES the original array.  For this reason, the sortProton function only needs to be called
        #once each time step, but there are many places where we'd need the protons to be sorted appropriately and automatically
        #so we'll just have to work on speed ups in here rather than frugal calling of this method.
        #print 'sorting protons'
        if self.name not in DeprotonatedWaterDimer:
            print 'failed! wrong molecule!', end
        H0O1=self.bondlength(x,atom1=0 ,atom2=1)
        H0O3=self.bondlength(x,atom1=0 ,atom2=3)
        H2O1=self.bondlength(x,atom1=2 ,atom2=1)
        H2O3=self.bondlength(x,atom1=2 ,atom2=3)
        H4O1=self.bondlength(x,atom1=4 ,atom2=1)
        H4O3=self.bondlength(x,atom1=4 ,atom2=3)
        midpoint=(x[:,1,:]+x[:,3,:])/2.0
        H0M=self.mag(x[:,0,:]-midpoint)
        H2M=self.mag(x[:,2,:]-midpoint)
        H4M=self.mag(x[:,4,:]-midpoint)
        DistanceToMidPt=np.array(zip(H0M,H2M,H4M))
        
        H0H2=self.bondlength(x,atom1=0 ,atom2=2)
        H0H4=self.bondlength(x,atom1=0 ,atom2=4)
        H2H4=self.bondlength(x,atom1=2 ,atom2=4)

        aveOH0=np.average(zip(H0O1,H0O3),axis=1)
        aveOH2=np.average(zip(H2O1,H2O3),axis=1)
        aveOH4=np.average(zip(H4O1,H4O3),axis=1)

        averagesAll=np.array(zip(aveOH0,aveOH2,aveOH4))

        OH1DistAll=np.array(zip(H0O1,H2O1,H4O1))
        sortByAveragesAll=np.argsort(averagesAll,axis=1)
        sortByDistToMP=np.argsort(DistanceToMidPt,axis=1)
        #checkSortNeed=np.logical_not(sortByAveragesAll[:,0]==0)
        

        


        checkSortNeed=np.logical_not(sortByDistToMP[:,0]==0)
        
        #print 'checkSortNeed sample', sortByAveragesAll[0:10],checkSortNeed[0:10]
        listOfSwapped=[]
        if np.any(checkSortNeed):
            #print np.where(checkSortNeed),
            #fileout=open('swappyCoordinates.xyz','a')
            for m in np.where(checkSortNeed):
                n=m[0]
                sortByAverages=sortByAveragesAll[n]
                sortByMPdist=sortByDistToMP[n]
                
                protonIndices=np.array([0,2,4])
                averages=averagesAll[n]
                OH1Dist=OH1DistAll[n]
                
                #centralProtonIndex=protonIndices[sortByAverages][0]
                centralProtonIndex=protonIndices[sortByMPdist][0]
                #outerOHIndex=protonIndices[sortByAverages][1:]
                outerOHIndex=protonIndices[sortByMPdist][1:]
                #outerOHDist=OH1Dist[sortByAverages][1:]
                outerOHDist=OH1Dist[sortByMPdist][1:]

                sortByHO1Dist=np.argsort(outerOHDist)
                H2primeIndex=outerOHIndex[sortByHO1Dist][0]
                H4primeIndex=outerOHIndex[sortByHO1Dist][1]

                positionH0prime=np.argmin(averages)*2
                positionH2prime=np.argmin(OH1Dist)*2
                positionH4prime=np.argmax(OH1Dist)*2
                if not (centralProtonIndex==0 and H2primeIndex==2 and H4primeIndex==4):
                    print 'walkN',n,
                    print 'AverageOH: ', averages,
                    print 'O1-H dis: ',OH1Dist,
                    print 'O2-H dis: ',np.array([H0O3[n],H2O3[n],H4O3[n]]),
                    print 'HH distances', H0H2[n],H0H4[n],H2H4[n],
                    print 'Distance to midpoint:', DistanceToMidPt[n],
                    print 'Order from sort by averages',sortByAverages,'order from sort by dist to MP',sortByDistToMP[n]
                    #print centralProtonIndex,H2primeIndex,H4primeIndex, '=?=',            
                    #print positionH0prime,positionH2prime, positionH4prime
                    #print x[n]
                    #self.printCoordsToFile([x[n]],fileout)
                    print 'no swap!'
                    #x[n][[0,1,2,3,4]]=x[n][[centralProtonIndex,1,H2primeIndex,3,H4primeIndex]]
                    #print 'yes swap!'
                    # self.printCoordsToFile([x[n]],fileout)
                    #print 'finally \n',x[n]
                    listOfSwapped.append(n)
                    
        #I might not have to sort all of them!
        
            #fileout.close
        return listOfSwapped

    def printCoordsToFile(self,x,fileout):
        au2ang=0.529177249
        fakeMoleculeNames=['H','O','Li','N','Be']
        for particle in x:
            fileout.write(str(self.nAtoms)+' \n'+' \n')
            for atomName, atom in zip(fakeMoleculeNames,particle):
                fileout.write(str(atomName)+'   '+str(au2ang*atom[0])+"   "+str(au2ang*atom[1])+"   "+str(au2ang*atom[2])+"\n")
            fileout.write("\n")
        return

    def calcAverageInternalCoordinates(self,x,dw):
        if self.name in DeprotonatedWaterDimer:
            #listOfSwapped=self.sortProtons(x)
            #print 'check swapped:', x[listOfSwapped]
            #print '\n ^^^ no really check it! ^^^ \n'
        #Local Intramolecular:                                                                                                                 
            HO1=self.bondlength(x,atom1=1, atom2=2)
            HO2=self.bondlength(x,atom1=3, atom2=4)
            magAsOH=np.absolute(HO2-HO1)
        #shared proton                                                                                                                         
            BO1=self.bondlength(x,atom1=0, atom2=1)
            BO2=self.bondlength(x,atom1=0, atom2=3)
        #Intermolecular                                                                                                                        
            OO= self.bondlength(x,atom1=1, atom2=3)
            HxH=self.bondlength(x,atom1=2, atom2=4)
            H2B=self.bondlength(x,atom1=0, atom2=2)
            H4B=self.bondlength(x,atom1=0, atom2=4)
            
        #PseudoRock
            Rock1=self.bondlength(x,atom1=1, atom2=4)-self.bondlength(x,atom1=1, atom2=0)
            Rock3=self.bondlength(x,atom1=3, atom2=2)-self.bondlength(x,atom1=3, atom2=0)
        #calc max, min, average, expectationValue, and  std of each                                                                                                   
            Values=np.zeros((11,5))
            Values[:,0]=    np.min([HO1,HO2,magAsOH,BO1,Rock1,Rock3,BO2,OO,HxH,H2B,H4B],axis=1)
            Values[:,1]=    np.max([HO1,HO2,magAsOH,BO1,Rock1,Rock3,BO2,OO,HxH,H2B,H4B],axis=1)
            Values[:,2]=np.average([HO1,HO2,magAsOH,BO1,Rock1,Rock3,BO2,OO,HxH,H2B,H4B],axis=1)
            Values[:,3]=np.average([HO1,HO2,magAsOH,BO1,Rock1,Rock3,BO2,OO,HxH,H2B,H4B],axis=1,weights=dw)
            Values[:,4]=    np.std([HO1,HO2,magAsOH,BO1,Rock1,Rock3,BO2,OO,HxH,H2B,H4B],axis=1)
            
            internalNames=['HO1','HO2','|r2-r1|','BO1','BO2','Rock1','Rock3','OO','HxH','H2B','H4B']            
            
        return internalNames,Values

    def calcRocks(self,x):
        BO1=self.bondlength(x,atom1=1, atom2=0)
        BO2=self.bondlength(x,atom1=3, atom2=0)
        Rock1=self.bondlength(x,atom1=1, atom2=4)-BO1
        Rock3=self.bondlength(x,atom1=3, atom2=2)-BO2
        return Rock1,Rock3
    def calcOHBondLenghts(self,x):
        if self.name in DeprotonatedWaterDimer:
            #swap=self.sortProtons(x)
            OH1,OH2=self.calcLocalOH(x)
            return OH1,OH2,self.calcStretchSym(x),self.calcStretchAnti(x)
        else:
            OH1=self.bondlength(x,atom1=1, atom2=2)
            OH2=self.bondlength(x,atom1=3, atom2=4)
            invSqrt2=1.0/np.sqrt(2.0)
            OHSym=invSqrt2*(OH1+OH2)
            OHAsym=invSqrt2*(OH1-OH2)
            return OH1, OH2, OHSym, OHAsym

    def calcSharedProtonDisplacement(self,x):
        if self.name in ProtonatedWaterDimer:
            r1=self.bondlength(x,atom1=2, atom2=1)
            r2=self.bondlength(x,atom1=2, atom2=0)
            return r2-r1
        elif self.name in DeprotonatedWaterDimer:
            r1=self.bondlength(x,atom1=0, atom2=1)
            r2=self.bondlength(x,atom1=0, atom2=3)#ha                          
            return r2-r1

    def calcStretchAntiIn(self,x):

        if self.name in ProtonatedWaterDimer:
            r1=self.bondlength(x,atom1=0, atom2=3)
            r2=self.bondlength(x,atom1=0, atom2=4)
            r3=self.bondlength(x,atom1=1, atom2=5)
            r4=self.bondlength(x,atom1=1, atom2=6)
            return 0.5*(r1+r2-r3-r4)

    def calcStretchAnti(self,x):
        #print 'calculating StretchAnti'
        if self.name in DeprotonatedWaterDimer:
            #print 'calculatingStretchAnti',
            #listOfSwapped=self.sortProtons(x)
            #listOfSwapped=[]
            r1=self.bondlength(x,atom1=1,atom2=2)
            r2=self.bondlength(x,atom1=3,atom2=4)
            
            #print '3 averages',np.average(r1), np.average(r2) , np.average(r1-r2), ' --- '
            #return (r1-r2), listOfSwapped
            return np.sqrt(0.5)*(r1-r2)#, listOfSwapped

    def calcStretchSym(self,x):
        if self.name in DeprotonatedWaterDimer:
            r1=self.bondlength(x,atom1=1,atom2=2)
            r2=self.bondlength(x,atom1=3,atom2=4)
            return np.sqrt(1.0/2.0)*(r1+r2)
    def calcLocalOH(self,x):
        if self.name in DeprotonatedWaterDimer:
            return self.bondlength(x,atom1=1,atom2=2),self.bondlength(x,atom1=3,atom2=4)
    
    def calcZdisplacement(self,x):

        # define midpoint
        OOMP=(x[:,1]+x[:,3])/2.0

        # define vector between O1 and MP
        OMPVec=x[:,1]-OOMP

        # define H-OOMPvector
        HMP= x[:,0]-OOMP

        # calc projection of H onto O-MP vector, and the tada!
        projection=np.zeros(x.shape[0])
        for i,(omp,hmp) in enumerate(zip(OMPVec,HMP)):
            projection[i]=np.dot(hmp,omp)
            projection[i]=projection[i]/np.linalg.norm(omp)

        #if np.any((np.absolute(projection)>2.0)):
        #    print 'long here',np.where((np.absolute(projection)>2.0))
        #    index=np.where((np.absolute(projection)>2.0))[0,0]
        #    print 'for x[,',index,']\n',x[index]
        #    print 'the midpoint is ', OOMP[index]
        #    print 'the midpoint to oxygen vector is ', OMPVec[index]
        #    print 'the midpoint to hydrogen vector is', HMP[index]
        #    print 'and the magnitude of that vector is ', np.linalg.norm(HMP[index])
        #    print 'the projections is', projection[index]
        #mass is 1/mH +1/2mO
            
        return projection

    def calcRn(self,x):
        #listOfSwapped=self.sortProtons(x)
        if self.surfaceName=='SharedProton':
            rncoord=self.calcSharedProtonDisplacement(x)
        elif self.surfaceName=='StretchAntiIn':
            rncoord=self.calcStretchAntiIn(x)
            return rncoord
        elif self.surfaceName=='OHStretchAnti':
            #print 'from calcRN',
            rncoord=self.calcStretchAnti(x)

        elif self.surfaceName=='LocalOHStretch':
            rncoord=AVERAGEGroundStateOH-self.calcLocalOH(x)

        elif self.surfaceName=='Z-displacement':
            rncoord=self.calcZdisplacement(x)
        else:
            print 'surface name is not found!', end
            
        return rncoord#,listOfSwapped

    def bondlength(self,pos,atom1=1,atom2=3):
        length=(pos[:,atom1,0]-pos[:,atom2,0])**2+(pos[:,atom1,1]-pos[:,atom2,1])**2+(pos[:,atom1,2]-pos[:,atom2,2])**2
        length=np.sqrt(length)
        return length

    def mag(self,xList):
        magnitude=np.zeros(xList.shape[0])
        for i,x in enumerate(xList):
            magnitude[i]=np.sqrt(x[0]*x[0]+x[1]*x[1]+x[2]*x[2])
        return magnitude

