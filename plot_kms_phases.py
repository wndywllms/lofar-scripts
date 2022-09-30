#!/usr/bin/env python

import matplotlib as mpl
mpl.use('Agg')
from itertools import product as ItP
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('SolutionsFile', type=str, help='kms solutions files')
args = parser.parse_args()

rad2deg = 360.0/(2*np.pi)
print rad2deg
FileName = args.SolutionsFile
dirs = FileName.split('/')
Name = dirs[0]+"/"+dirs[1]+"-"+FileName[FileName.find('killMS.')+7 : FileName.find('.sols')]



SolsDico=np.load(FileName)
Sols=SolsDico["Sols"]
Sols=Sols.view(np.recarray)

nt,nch,na,nd,_,_=Sols.G.shape
print nt,nch,na,nd
print Sols.G.shape
DirList=range(nd)
Antlist = range(na)
nSol=1
LSols=[Sols]





def plot_phase(h5parmname, solset, soltab, pol, refant='CS001LBA', norm=True, filename='phases'):
    h5 = h5parm.h5parm(h5parmname)
    hsols = h5.getSolset(solset)

    phases = hsols.getSoltab(soltab).getValues()
    phaseAx = phases[1]
    phases = phases[0]

    poli = np.where(phaseAx['pol']==pol)[0][0]
    if refant != '':
        refanti = np.where(phaseAx['pol']==pol)[0][0]
        
        phaseref = phases[:,refanti,:,poli]
    else:
        phaseref = np.zeros_like(phases[:,0,:,poli])

    xvals = phaseAx['time']
    yvals = phaseAx['freq'] /1.e6
    xvals = (xvals - xvals[0]) /3600.
    f, axa = plt.subplots(nrows=6, ncols=7, sharex=True, sharey=True, squeeze=True, figsize=(20,15))
    f.subplots_adjust(hspace=0, wspace=0,  top=0.95, bottom=0.05, left=0.05)
    cmesh=True
    # axes label
    if len(axa.shape) == 1: # only one row
        [ax.set_xlabel('time [hr]') for ax in axa[:]]
        axa[0].set_ylabel('freq [MHz]')
    else:
        [ax.set_xlabel('time [hr]') for ax in axa[-1,:]]
        [ax.set_ylabel('freq [MHz]') for ax in axa[:,0]]

    axs = axa.flatten()
    for anti in range(len(phaseAx['ant'])):
        ax = axs[anti]
        if norm:
            vals = normalize_phase(phases[:,anti,:,poli]-phaseref).T
        else:
            vals = (phases[:,anti,:,poli]-phaseref).T
        #vals.filled(np.nan)
        #ax.imshow(().T, origin='lower left', vmin=-3.14, vmax=3.14, cmap=plt.cm.jet)
        bbox = ax.get_window_extent().transformed(f.dpi_scale_trans.inverted())
        aspect = str((0.9*(xvals[-1]-xvals[0])*bbox.height)/((yvals[-1]-yvals[0])*bbox.width))
            
        im = ax.imshow(vals, origin='lower', interpolation="none", cmap=plt.cm.jet, norm=None, extent=[xvals[0],xvals[-1],yvals[0],yvals[-1]], aspect=str(aspect), vmin=-3.1416, vmax=3.1416)
        #colorbar()
        stdev = np.nanstd(vals)
        mean = np.nanmean(vals)
        valsc = sigmaclip(vals[np.isfinite(vals)].flatten(), 5.,5.)
        stdevs = np.nanstd(valsc.clipped)
        means = np.nanmean(valsc.clipped)
        print '{:s} {:.3f} {:.3f}'.format(phaseAx['ant'][anti], mean, stdev)
        #print '{:s} {:.3f} {:.3f}'.format(phaseAx['ant'][anti], means, stdevs)
        ax.text(.5, .9, phaseAx['ant'][anti], horizontalalignment='center', fontsize=14, transform=ax.transAxes)
        ax.text(.5, .8, 'stdev={:.2f}'.format(stdev), horizontalalignment='center', fontsize=14, transform=ax.transAxes)
        
    f.colorbar(im, ax=axa.ravel().tolist(), use_gridspec=True, fraction=0.02, pad=0.005, aspect=35)
    #f.tight_layout()
    f.savefig(filename+'.png', bbox_inches='tight')
    
    f, axa = plt.subplots(nrows=6, ncols=7, sharex=True, sharey=False, squeeze=True, figsize=(20,15))
    axs = axa.flatten()
    for anti in range(38):
        ax = axs[anti]
        if norm:
            vals = normalize_phase(phases[:,anti,:,poli]-phases[:,refanti,:,poli]).T
        else:
            vals = (phases[:,anti,:,poli]-phases[:,refanti,:,poli]).T
        ax.hist(vals.flatten(), bins=200, histtype='step', range=(-3.14, 3.14))
    f.subplots_adjust(hspace=0, wspace=0, top=0.95, bottom=0.05, left=0.05)
    f.tight_layout()
    



for iDir in DirList:
    print '%d of %d' %(iDir+1,nd)
    
    Nstat = len(Antlist)
    Nr = int(np.ceil(np.sqrt(Nstat)))
    Nc = int(np.ceil(np.float(Nstat)/Nr))
    fp, axa = plt.subplots(Nr, Nc, sharex=True, sharey=True, figsize=(16,12))
    
    if len(axa.shape) == 1: # only one row
        [ax.set_xlabel('time [hr]') for ax in axa[:]]
        axa[0].set_ylabel('phase [deg]')
    else:
        [ax.set_xlabel('time [hr]') for ax in axa[-1,:]]
        [ax.set_ylabel('phase [deg]') for ax in axa[:,0]]
    
    axs = axa.flatten()
    
    iAntref = 0
    
    iChan = nch-1
    G=Sols.G[:,iChan,:,iDir,:,:]
    Jref=G[:,iAntref,:,:]
    J00ref=Jref[:,0,0]; J11ref=Jref[:,1,1]
    J00ref*=J00ref[0].conj()/np.abs(J00ref[0])
    J11ref*=J11ref[0].conj()/np.abs(J11ref[0])
    for iAnt in Antlist:
        axsp = axs[iAnt]
        #    if iDir != 10:
        #        continue
        #iAnt=5
        op0=np.angle
        op1=None
        iSol = 0
        iChan = nch-1
        Sols=LSols[iSol]
        G=Sols.G[:,iChan,:,iDir,:,:]
        J=G[:,iAnt,:,:]
        J00=J[:,0,0]; J11=J[:,1,1]
        J00*=J00[0].conj()/np.abs(J00[0])
        J11*=J11[0].conj()/np.abs(J11[0])
        
        freq = np.mean(SolsDico['FreqDomains'][iChan])
    
        dtec0 = op0(J00)*freq/(-8.4479745e9)
        dtec1 = op0(J00)*freq/(-8.4479745e9)

    
        plottec = False
        # For TEC
        if plottec == True:
            axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),dtec0,color='b')#,linestyle='None')
            axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),dtec1,color='g')#linestyle='None')
            axsp.set_ylabel('dTEC')

        # For Phases
        else:
            axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),(op0(J00)-op0(J00ref))*rad2deg,color='b')#,linestyle='None')
            axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),(op0(J11)-op0(J11ref))*rad2deg,color='g')#linestyle='None')
            #axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),(op0(J00)-op0(J00ref))*rad2deg,color='b')#,linestyle='None')
            #axsp.plot((Sols.t0-np.min(Sols.t0))/(60.0*60.0),(op0(J11)-op0(J11ref))*rad2deg,color='g')#linestyle='None')
            #axsp.set_ylabel('Phase (deg)')  
            #print np.max(op0(J00)*rad2deg),np.max(op0(J00))
            axsp.set_ylim(ymin=-180,ymax=180)
    
        axsp.text(.5, .9, SolsDico['StationNames'][iAnt], horizontalalignment='center', fontsize=12, transform=axsp.transAxes)
        #axsp.set_xlabel('Time (s)')
        #axsp.set_xlim(xmin=0.0,xmax=8.0)
        
    plt.subplots_adjust(wspace=0,hspace=0,left=0.05,right=0.98,bottom=0.05,top=0.98)
    plt.savefig('%s-iDir%s.png'%(Name,iDir))
    #plt.close()
    #plt.cla()

    
    
