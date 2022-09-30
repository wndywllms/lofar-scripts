from __future__ import print_function

import os
import sys
import numpy as np
import pyrap.tables as pt

def check_flagged(ms):
    t = pt.table(ms, readonly=True)
    tc = t.getcol('FLAG').flatten()
    return float(np.sum(tc))/len(tc)

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='concat_and_split')
    parser.add_argument('--datacolumn', help='datacolumn', default='CORRECTED_DATA', type=str)
    parser.add_argument('--skipconcat', help='skipconcat', default=False, action='store_true')
    parser.add_argument('--skipsplit', help='skipsplit', default=False, action='store_true')
    parser.add_argument('--keepfiles', help='keep intermediate files', default=False, action='store_true')
    parser.add_argument('--noclobber', help='clobber is off', default=False, action='store_true')
    parser.add_argument('--dryrun', help='only print commands', default=False, action='store_true')
    parser.add_argument('--subnchan', help='number of channels in each band', default=40, type=int)
    parser.add_argument('-s','--suffix', help='add a suffix to the obsid', default='', type=str)
    parser.add_argument('-p','--prefix', help='add a prefix to the obsid', default='', type=str)
    parser.add_argument('outmsroot', help='Output MS root name', type=str)
    parser.add_argument('inmsfile', help='Measurement sets', nargs='+', type=str)
    args = parser.parse_args()
    
    inmsfiles = args.inmsfile
    datacolumn = args.datacolumn
    suffix = args.suffix
    prefix = args.prefix

    outmsroot = prefix + args.outmsroot + suffix
    
    nchan = None
    
    


    if not args.skipsplit:

        allms = []
        for inms in inmsfiles:
            
            fl = check_flagged(inms)
            print (inms,fl,'flagged fraction')
            
            # get basename of this ms
            inmsroot = inms.split('/')[-1].split('.')[0]
            print('input ms root: ',inmsroot)
            # fra code T00.MS etc
            if inmsroot[0] == 'T':
                inmsroot = outmsroot+'_'+inmsroot

            ### split in freq
            subnchan=args.subnchan
            # all should be the same so we do this once
            if nchan is None:
                t0_spw = pt.table(inms+'/SPECTRAL_WINDOW')
                nchan = t0_spw.getcol('NUM_CHAN')[0]
                fchan = t0_spw.getcol('CHAN_FREQ')[0]
                dchan = t0_spw.getcol('CHAN_WIDTH')[0]
                
            # keep a list of the bands created for this timechunk
            allmsi = []
            for ii,i in enumerate(range(0,nchan,subnchan)):
                outmsband = '{prefix}{inmsroot}{suffix}_BAND{ii:03d}.ms'.format(ii=ii, inmsroot=inmsroot, suffix=suffix,prefix=prefix)
                #print('Out MS band',outmsband)
                #cmd= 'DPPP numthreads=32 msin={inms} msin.datacolumn={datacolumn} msout={outmsband} steps=[filter] filter.type=filter  filter.startchan={i:d} filter.nchan={subnchan:d}'.format(i=i,subnchan=subnchan, inms=inms, outmsband=outmsband, datacolumn=datacolumn)
                print(inms+' -> '+outmsband)
                #if not args.dryrun:
                    #print(cmd)
                    #os.system(cmd)
                allmsi.append(outmsband)
                
            startchans = [str(i) for i in range(0,nchan,subnchan)]
            # run DPPP in one - with filter so read is done once...
            cmd = 'DPPP msin={inms} msin.datacolumn={datacolumn} msout=. steps=[split] split.steps=[filter,out] split.replaceparms=[filter.startchan,out.name] filter.startchan=[{startchans}] filter.nchan={subnchan} out.name=[{msouts}]'.format(inms=inms, datacolumn=datacolumn, msouts=','.join(allmsi), startchans=','.join(startchans), subnchan=subnchan)
            print(cmd)
            if not args.dryrun:
                
                s = os.system(cmd)
                if s != 0:
                    if fl == 1:
                        print('DPPP run failed, trying again with DATA column - happens if all flagged')
                        
                        
                        cmd = 'DPPP msin={inms} msin.datacolumn={datacolumn} msout=. steps=[split] split.steps=[filter,out] split.replaceparms=[filter.startchan,out.name] filter.startchan=[{startchans}] filter.nchan={subnchan} out.name=[{msouts}]'.format(inms=inms, datacolumn='DATA', msouts=','.join(allmsi), startchans=','.join(startchans), subnchan=subnchan)
                        print(cmd)
                        if not args.dryrun:
                            
                            s = os.system(cmd)
                        
                
                
            # add this list to the list of all
            allms.append(allmsi)
        




    allms = np.array(allms)
    print(allms)
    #sys.exit()
    
    
 
    
    if not args.skipconcat:
        ### concatenate in time
        
        # for each of the bands created above
        for bandi in range(allms.shape[1]):
        
            mergems = '{outmsroot}_BAND{ii:03d}.ms'.format(ii=bandi, outmsroot=outmsroot)
            
                    
            if os.path.isdir(mergems):
                if args.noclobber==False:
                    print ('removing existing ms: '+mergems )
                    os.system('rm -rf '+mergems)
                else:
                    print ('ms '+mergems+' exists and noclobber is set True')
                    sys.exit()
            
            
            print('concatenating in time')
            print(mergems+': '+','.join(allms[:,bandi]))
            if not args.dryrun:
                t = pt.table(allms[:,bandi])
                t.sort('TIME,ANTENNA1,ANTENNA2').copy(mergems, deep=True)
            
                print('concatenating done')

                print('add imaging columns')
                pt.addImagingColumns(mergems)

                # remove the intermediate files unless asked to keep them
                if not args.keepfiles:
                    for ms in allms[:,bandi]:
                        print('removing '+ms)
                        os.system('rm -rf '+ ms)
        
