import numpy as np
from matplotlib import pyplot as plt
import time
# Energy in MeV, dx in cm

m_positrc2 = 0.511  #MeV
m_electrc2 = m_positrc2
M_protonc2 = 938 #MeV
r_e = 2.82e-13  #cm - raggio classico elettone
N_av = 6.022e23 #mol^-1 - Numero di avogadro
density = 1  #g/cm3 - densità acqua

Z = 7.42 # Z efficace H2O
A = 18

N_e = density * N_av *Z/A

I = (12*Z + 7)*1e-6 #MeV

#Robe utili per il calcolo dei raggi delta:
W_min = 0.01 #[MeV] = 10 keV energia minima del delta, affinchè venga prodotto



def SamplingE0(isotope):

    def Distr_energie(E, z, emax):
        Energy = E + m_electrc2
        pc = np.sqrt(Energy**2 - m_positrc2**2)
        eta = -z*E/(137*pc)
        F_ze = 2*np.pi*eta/(1-np.exp(-2*np.pi*eta))
        n_e = F_ze * pc * E * (emax-E)**2
        return n_e
    
    if isotope == 'F18':
        z = 10
        E_endpoint = 0.635
        h = 0.250
    elif isotope == 'C11':
        z = 7
        E_endpoint = 0.970
        h = 0.39
    elif isotope == 'N13':
        z = 8
        E_endpoint = 1.190
        h = 0.49
    elif isotope == 'O15':
        z = 9
        E_endpoint = 1.72
        h = 0.74
    
    found = False
    while found is False:
        E_k = np.random.uniform(0, E_endpoint)
        y = np.random.uniform(0, h+0.1)
        if y < Distr_energie(E_k, z, E_endpoint):
            found = True
    return E_k

def dedx_coll(E_kin): #E_kin in MeV

    Energy = E_kin + m_positrc2
    beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy
    
    coll1 = 2*np.pi* N_av * r_e**2 * m_electrc2 /beta**2 * density*Z/A
    tau = E_kin/m_electrc2
    taup2 = tau + 2
    F_tau = 2*np.log(2) - beta**2 /12 * (23 + 14/taup2 + 10/taup2**2 + 4/taup2**3) # per positroni
    #F_tau = 1-beta**2 + (tau**2 /8 - np.log(2)*(2*tau+1))/(tau+1)**2 # per elettroni
    coll2 = np.log(tau**2 * taup2/( 2*(I/m_electrc2)**2 )) + F_tau
    
    coll = coll1 * coll2
    return coll

def Step(Estep, E_kin):
    r = Estep/dedx_coll(E_kin)
    return r

def Ndelta(E_kin, step):
    '''
    Prende in input l'energia cinetica della particella incidente (E_kin), 
    e la lunghezza dello step, spazio percorso, e restituisce il numero di 
    elettroni delta prodotti in quel tragitto "step"
    '''
    W_min = 10e-3 #[MeV] : 10keV come energia minima di produzione

    if E_kin > W_min:
        Energy = E_kin + m_electrc2
        beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy
        
        AA = N_e * 2*np.pi* r_e**2 * m_electrc2 #primo pezzo, senza il beta al denom
        tau = E_kin/m_electrc2
        W_max = 2*tau*(tau +2)*m_electrc2/(2+ 2*(tau+1))
        G = (W_max-W_min)/(Energy)**2
        B = (1/W_min - 1/W_max) - beta**2 *np.log(W_max/W_min)/W_max + G
        dndx = AA/beta**2 * B
        N_delta = dndx * step
    else: N_delta = 0
    
    return N_delta

def Phidelta(w, E_kin):
    '''
    Data l'energia w del delta creato e l'energia E_kin, da cui ricavo beta della
    particella incidente, ricavo l'angolo di emissione del delta: phi
    '''
    Energy = E_kin + m_electrc2
    beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy

    phi = np.arccos(np.sqrt(w/(2*m_electrc2*beta**2)))
    '''
    dato che l'angolo del delta può essere sopra o sotto la direzione di incidenza, 
    estraggo un numero 0 o 1, per stabilire se il delta va a + 0 - phidelta
    '''
    temp = np.random.randint(2)
    if temp == 0:
        phi = -phi
    return phi

def Phipositr(w, e_kin, phidelta):
    '''
    Calcola l'angolo di emissione del positrone dopo l'urto che ha creato un raggio
    delta, imponendo la conservazione dell'impulso,  dato e_kin = energia cinetica
    positrone incidente, w = energia cinetica del delta, phidelta = angolo di emissione del 
    delta, rispetto alla direzione di incidenza del positrone
    '''
    energy = e_kin + m_electrc2
    energy_prim = e_kin - w + m_electrc2
    energy2 = w + m_electrc2
    p1 = np.sqrt(energy**2 - m_electrc2**2)
    p1_prim = np.sqrt(energy_prim**2 - m_electrc2**2)
    p2_prim = np.sqrt(energy2**2 - m_electrc2**2)

    #cosphi1 = -p2_prim*np.cos(phidelta)/p1_prim
    sinphi1 = -p2_prim*np.sin(phidelta)/p1_prim
    if sinphi1>1:
        sinphi1 =1
    elif sinphi1 < -1:
        sinphi1 = -1
    phipositr = np.arcsin(sinphi1)
    return phipositr

def Rotation(theta, vect_prim):
    rot_mat = np.array([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
    #vect_prim = np.array([[x_prim], [y_prim]])
    vect = np.dot(rot_mat, vect_prim)
    vect = np.ravel(vect)
    return vect
    
def Traslation(vect_prim, vect_o_prim):
    vect_trasled = vect_prim + vect_o_prim
    return vect_trasled 
    
def SamplingEkinDelta(E_kin):
    W_min = 0.01 #[MeV] energia necessaria per creare un delta, limite inferiore dell'intervallo
    Energy = E_kin + m_electrc2
    beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy
    tau = E_kin/m_electrc2
    W_max = 2*tau*(tau +2)*m_electrc2/(2+ 2*(tau+1))

    flag = False

    if E_kin > W_min:
        while(flag is False):
            '''
            estraggo a caso una energia del delta W, usando
            rigetto elementare. uso una flag per stabilire quando
            ho trovato un valore valido della distribuzione delle 
            energie, cioè un valore valido dell'energia del delta
            '''
            W = np.random.uniform(W_min, W_max)
            p_w = 1/(beta**2 * W**2) - 1/(W*W_max)
            h = 1/W_min**2 - 1/(W_min*W_max)
            y = np.random.uniform(0, h)
            if y < p_w:
                flag = True
    else: W = 0
    return W

def DeltaPosition(vett_inizio, vett_fine):
     '''
     Estrae a caso un valore per stabilire il punto di creazione del raggio delta, 
     tra il punto di inizio e il punto di fine dello step fatto dal positrone, 
     scegliendo a caso un valore di x compreso tra i due valori di ascissa, 
     e la corrispondente ordinata data dall'equazione della retta passante per quei
     due punti (inizio e fine step)
     '''
     x_inizio = vett_inizio[0]
     y_inizio = vett_inizio[1]
     x_fine = vett_fine[0]
     y_fine = vett_fine[1]
    
     if x_inizio == x_fine:
         x_delta = x_inizio
         y_delta = np.random.uniform(y_inizio, y_fine)
     else:
         x_delta = np.random.uniform(x_inizio, x_fine)
         y_delta = y_inizio + (y_fine - y_inizio)*(x_delta - x_inizio)/(x_fine - x_inizio)

     vett_delta = np.array([x_delta, y_delta])
     return vett_delta
     
def SamplingMultipleScattering(dx, E_kin):
    '''
    dx = step [cm]
    E_kin = energia cinetica particella primaria [Mev]
    Prende in input la lunghezza dello step e l'energia cinetica della particella primaria
    e calcola la distribuzione dell'angolo di multiple scattering, la campiona e restituisce 
    l'angolo di scattering in radianti
    '''
    Energy = E_kin + m_electrc2
    beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy
    momentum = np.sqrt(Energy**2 - m_positrc2**2)

    alpha = 1/137
    F = 0.98
    xi_c2 = 0.157 * (Z*(Z+1)/A)*dx*density /(momentum*beta)**2
    xi_a2 = 2.007e-5 * Z**(2/3) * (1+3.34*(Z*alpha/beta)**2)/momentum**2
    omega = xi_c2/xi_a2
    v = 0.5*omega/(1-F)
    
    theta_ms = 2*xi_c2/(1+F**2) * ((1+v)/v *np.log(1+v) - 1)

    theta_max = np.pi #[rad]
    
    p = np.random.random()
    norm = 1-np.exp(-theta_max**2/theta_ms)
    theta_rand = np.sqrt(theta_ms * np.log(1/(1-norm*p)))

    return theta_rand

def SamplingGauss(dx, E_kin):
    '''
    dx = step [cm]
    E_kin = energia cinetica particella primaria [Mev]
    Prende in input la lunghezza dello step e l'energia cinetica della particella primaria
    e calcola la distribuzione dell'angolo di multiple scattering, la campiona e restituisce 
    l'angolo di scattering in radianti
    '''
    Energy = E_kin + m_electrc2
    beta = np.sqrt(Energy**2 - m_positrc2**2)/Energy
    momentum = np.sqrt(Energy**2 - m_positrc2**2)

    alpha = 1/137
    F = 0.98
    xi_c2 = 0.157 * (Z*(Z+1)/A)*dx*density /(momentum*beta)**2
    xi_a2 = 2.007e-5 * Z**(2/3) * (1+3.34*(Z*alpha/beta)**2)/momentum**2
    omega = xi_c2/xi_a2
    v = 0.5*omega/(1-F)
    
    theta_ms = 2*xi_c2/(1+F**2) * ((1+v)/v *np.log(1+v) - 1)
    thetax_ms = theta_ms/2
    std_dev = np.sqrt(thetax_ms)   
    def Gauss(x, sigma):
        return 1/np.sqrt(2*np.pi*sigma**2) * np.exp(-x**2/(2*sigma**2))
    theta_max = 10*np.pi/180 # [rad], 10 gradi di angolo massimo
    h = 1/np.sqrt(2*np.pi*std_dev**2) #altezza massima della gaussiana
    found = False
    while(found is False):
        theta_rand = np.random.uniform(-theta_max, theta_max)
        p = Gauss(theta_rand, std_dev)
        y = np.random.uniform(0, h)
        if y < p:
            found = True
    return theta_rand
 
#if __name__ == “main”: 

# Ekin = energia cinetica della particella (elettrone o positrone) primaria

#seed = time.time()
seed = 42
np.random.seed(int(seed))

    
Estep = 1e-3 # MeV - Energia persa ad ogni step

#Creo array per tener conto della fine del percorso del positrone
X_end = []
Y_end = []


Tot_Npositr = 10000

text_file = open("endpoints.txt", "w")
text_file.write('#x_endpoint   y_endpoint \n')
for npart in range(Tot_Npositr):
    if npart%10==0:
        print(npart)
    delta_parameters = np.zeros((10, 5))
    i_delta = 0

    first_iteration = True
    #Creo array dove tener conto della posizione della particella punto per punto, per ciascuna particella
    X = []
    Y = []



    #Ekin iniziallizzo l'energia CINETICA (Ekin) della particella con E_0
    E_0 = SamplingE0('F18') #Mev, energia iniziale positrone creato. Scegliere come argomento stringhe: 'F18', 'C11', 'N13', 'O15'
    Ekin = E_0
    
    while(Ekin > Estep):
        step = Step(Estep, Ekin)
        if step < 0:
            #DEBUGGARE QUESTA PARTE
            print('Step = cm', step)


        if first_iteration:
            posiz = np.array([0, 0])
            X.append(posiz[0])
            Y.append(posiz[1])
            theta_prim = np.random.uniform(0, 2*np.pi)
            theta0 = 0

            first_iteration = False
            delta = False
        elif delta:
            delta = False  
        else:
            theta_prim = SamplingGauss(step, Ekin)

        x1_prim, y1_prim = step*np.cos(theta_prim), step*np.sin(theta_prim)
        vett_prim = np.array([x1_prim, y1_prim])
        vett = Rotation(theta0, vett_prim) + posiz
        
        #Viene creato in questo tratto di strada? y/n
        '''Calcolo quanti raggi delta vengono creati, tramite la funzione
        Ndelta. Dato che per ciascuno step, il numero di raggi delta creati, 
        ricavato con la formula, è < 1 (typ: 0.018), per stabilire st un delta 
        viene creato o no, estraggo un numero uniforme tra 0 e 1, e se il numero
        è minore del numero ricavato prima, vuol dire che il raggio delta è 
        stato creato. 
        '''
        ndelta = Ndelta(Ekin, step)
        #mettere un controllo che ndelta sia < 1 ?
        yndelta = np.random.uniform(0, 1)
        #yndelta = ndelta + 1 #Elimino la creazione di delta
        if yndelta < ndelta: #SE VIENE CREATO IL DELTA
            # 1: In che punto viene creato il delta.
            delta_position = DeltaPosition(posiz, vett)
            # 2: Con che energia CINETICA (Ekin_delta) viene creato il delta.
            Ekin_delta = SamplingEkinDelta(Ekin)
            # 3: Calcolo l'angolo di emissione del delta
            phidelta = Phidelta(Ekin_delta, Ekin)
            # 4: Calcolo il corrispondente angolo di emissione del positrone
            phipositr = Phipositr(Ekin_delta, Ekin, phidelta)
            # Inizia il pezzo in cui stabilisco la traiettoria del positrone dopo l'urto col delta
            posiz = delta_position
            X.append(posiz[0])
            Y.append(posiz[1])
            Ekin -= Ekin_delta
            theta0 += theta_prim
            theta_prim = phipositr
            delta = True
            # E ora salvo i parametri del delta per utilizzarli dopo
            delta_parameters[i_delta][0] = Ekin_delta
            delta_parameters[i_delta][1] = delta_position[0]
            delta_parameters[i_delta][2] = delta_position[1]
            delta_parameters[i_delta][3] = theta0
            delta_parameters[i_delta][4] = phidelta
            i_delta += 1
            


        else:
            posiz = vett            
            X.append(posiz[0])
            Y.append(posiz[1])
            Ekin -= Estep
            theta0 += theta_prim
         
    X_end.append(X[-1])
    Y_end.append(Y[-1])
    text_file.write('%.6f  %.6f\n' %(X[-1], Y[-1]))

    plt.plot(X, Y, color = 'tab:blue')
    plt.xlabel('x [cm]')
    plt.ylabel('y [cm]')

    if delta_parameters.any() == 0:
        pass
    else:
        Tot_delta = i_delta
        for ndelta in range(Tot_delta):

            first_iteration = True
            #Creo array dove tener conto della posizione della particella punto per punto, per ciascuna particella
            X = []
            Y = []
            #Ekin iniziallizzo l'energia CINETICA (Ekin) della particella con E_0
            Ekin = delta_parameters[ndelta][0]
            while(Ekin > Estep):

                step = Step(Estep, Ekin)

                if first_iteration:

                    posiz = np.array([delta_parameters[ndelta][1], delta_parameters[ndelta][2]])
                    X.append(posiz[0])
                    Y.append(posiz[1])
                    theta_prim = delta_parameters[ndelta][4]
                    theta0 = delta_parameters[ndelta][3]

                    first_iteration = False 
                else:
                    theta_prim = SamplingGauss(step,Ekin) 

                x1_prim, y1_prim = step*np.cos(theta_prim), step*np.sin(theta_prim)
                vett_prim = np.array([x1_prim, y1_prim])
                vett = Rotation(theta0, vett_prim) + posiz

                posiz = vett            
                X.append(posiz[0])
                Y.append(posiz[1])
                Ekin -= Estep
                theta0 += theta_prim
            plt.plot(X, Y, color = 'tab:red')
            plt.xlabel('x [cm]')
            plt.ylabel('y [cm]')

text_file.close()  

        
plt.show()
