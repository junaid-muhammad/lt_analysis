      program calc_xsect


      implicit none

c This script computes the experimental cross section using the ratio
c DATA/MC(Yields * CS(MC)

c      character*2 prv_it
c      common prv_it

c      integer q2_bin
c      integer t_bin, phi_bin
c      common t_bin, phi_bin
      
c     Get number of the previous iteration.
      
c      if(iargc().ne.1) then
c         print*,'*** usage: calc_xsect prv_it ***'
c         stop
c      end if
c      call getarg(1,prv_it)

c     Calculate unseparated cross-sections. Now settings are for the piplus data (+)

      character*4 inp_pid
      integer inp_pol
      real inp_Q2, inp_W, inp_loeps, inp_hieps
      
      write(*,*) "Inputing particle, polarity, Q2, W and both epsilons:"
      read(*,*) inp_pid, inp_pol, inp_Q2, inp_W, inp_loeps, inp_hieps

      write(*,*) "PID = ",inp_pid,"POL = ",inp_pol,
     *           "Q2 = ",inp_Q2,"W = ",inp_W,
     *           "low_eps = ",inp_loeps,"high_eps = ",inp_hieps

      call xsect(inp_pid, inp_pol, inp_Q2, inp_W, inp_loeps)
      call xsect(inp_pid, inp_pol, inp_Q2, inp_W, inp_hieps)
      
      print*,  "-------------------------------------------------"
      
      stop
      end

*=======================================================================

      subroutine xsect(pid,npol_set,q2_set,w_set,eps_set)

      implicit none

      integer npol_set
      real q2_set,eps_set,w_set

      character*80 r_fn, kin_fn, mod_fn, par_fn
      character*80 xunsep_fn, xsep_fn
      character*2 pol
      character*4 pid

      integer it,ip
      real Eb,eps

      real q2_bin, w_bin
      integer t_bin, phi_bin
      
      integer nt,nphi

      real r,dr,w,dw,q2,dq2,tt,dtt,th_cm,th_pos
      real tm,tmn,tmx
      real eps_mod,th_mod,x_mod
      real x_real,dx_real

      integer ipol
      real th_pq

      real phi

      real, Dimension(9) :: t_bin_boundary

      character*80:: line
      
      integer i,j
      
      real par(16)
      real p,e
      
      character(len=100) :: fn_t_bins

!     Construct the file path using a format string
      write(fn_t_bins, '(a, a, i2.2, a, i3.3, a)') trim(pid),
     *     '/t_bin_interval_Q', nint(q2_set*10), 'W', nint(w_set*100)

!     Open the file
      open (unit=22, file=fn_t_bins, action='read')
      read (22, *) q2_bin, w_bin, t_bin, phi_bin

      nt = t_bin
      nphi = phi_bin
      
      read (22, '(A)') line  
      read(line, *) (t_bin_boundary(j), j = 1, t_bin + 1)

      close(22)
      
      ipol=0
      q2=0.
      eps=0.
      tmn=0.
      tmx=0.
      open(55,file=trim(pid) // '/list.settings')
      do while(ipol.ne.npol_set.or.q2.ne.q2_set.or.
     *     w.ne.w_set.or.eps.ne.eps_set)
         read(55,*) ipol,q2,w,eps,th_pq,tmn,tmx
      end do
      close(55)
      write(6,3)tmn,tmx
 3    format(' tmn, tmx: ',2f10.5)
      if(tmn.eq.0..or.tmx.eq.0.) 
     *     stop '*** setting is not found in list.settings'
                  
      if(npol_set.lt.0) then
         pol='mn'
      else
         pol='pl'
      end if
      print*,'polarity: ',pol
      
      Eb=0.
      open(56, file=trim(pid) // '/beam/Eb_KLT.dat')
      do while(.true.)
         read(56,*) Eb,q2,w,eps
         if(q2.eq.q2_set.and.w.eq.w_set.and.
     *     eps.eq.eps_set) go to 5         
      end do
 5    close(56)
      
      write(6,4)Eb,q2,w,eps,pol
 4    format(' xsect: Eb=',f8.5,
     *     '   at Q2=',f7.4,'   at W=',f7.4,
     *     '  eps=',f6.4,'  pol=',a2)

c     construct ratio data file name.

      write(r_fn,10) pid,pol,nint(q2*10),nint(w*100),nint(eps*100)
 10   format(a4,'/averages/aver.'
     *     ,a2,'_Q',i2.2,'W',i3.3,'_',i2,'.dat')
      print*,'       r_fn=',r_fn

      open(51,file=r_fn)

c     construct kinematics data file name.

      write(kin_fn,20) pid,nint(q2*10),nint(w*100)
 20   format(a4,'/averages/avek.Q',i2.2,'W',i3.3,'.dat')
      print*,'       kin_fn=',kin_fn

      open(52,file=kin_fn)

*     construct output file name.
      write(xunsep_fn,30) pid,pol,nint(q2_set*10),nint(w_set*100),
     *     nint(eps_set*100)
 30   format(a4,'/xsects/x_unsep.',a2,'_Q',
     *     i2.2,'W',i3.3,'_',i2,'.dat')
      print*,'       xunsep_fn=',xunsep_fn
c      pause
      
      open(61,file=xunsep_fn,status='replace')
      
      mod_fn='models/xmodel_' // trim(pid) // '_' // trim(pol) // '.f'
      print*,'xmodel: file=',mod_fn

*     Model fit parameters.

*** HERE!!      
*      write(par_fn,50) pid,pol,nint(q2_set*10),nint(w_set*100)
*     50   format(a4,'/parameters/par.',a2,'_Q',i2.2,'W',i3.3,'.dat')
*     print*, 'param: par_fn=',par_fn
      
      write(par_fn,50) pol
 50   format('models/par_',a2)      
      print*, 'param: par_fn=',par_fn
      
      do it=1,nt

         WRITE(*,*) '============'
         WRITE(*,*) 'Values read:'
         WRITE(*,*) '============'         
         read(52,*) w,dw,q2,dq2,tt,dtt,th_pos
         WRITE(*,*) 'Numtbins: ', nt
         WRITE(*,*) 'tbin: ', it
         WRITE(*,*) 'tmin: ', tmn
         WRITE(*,*) 'tmax: ', tmx
         WRITE(*,*) 't: ', tt
         
         tm=(t_bin_boundary(it) + t_bin_boundary(it+1)) / 2
         
         th_cm=th_pos

*     Convert back to radians
         th_cm=th_cm*3.14159D0/180.D0
         WRITE(*,*) 't-bin center: ', tm
         WRITE(*,*) 'th_cm (deg): ', th_cm*180./3.14159
         
         do ip=1,nphi

            phi=(ip-0.5)*2.*3.14159/nphi

*            if (phi.le.0.0) then
*               phi=phi+2.*3.14159
*            else if (phi.gt.2.*3.14159) then
*               phi=phi-2.*3.14159
*            end if
            
            read(51,*) r,dr
            
            call xmodel(pid,npol_set,Eb,q2_set,w_set,eps_set,
     *           w,q2,tm,phi,eps_mod,th_mod,x_mod,par_fn)

c angle check
            if (abs(th_mod-th_cm).gt.1.e-4) then
               write(6,*)' Angle error ',th_mod,th_cm
               stop
            endif

*     Set extreme ratio values to zero
            if (r.gt.10.0.or.r.le.0.1) then
               r=0.0
               dr=0.0
            endif
            
*     Convert from ub/MeV^2 to ub/GeV^2
            x_mod=x_mod*1.d+06
*     Convert from ub/GeV^2 to nb/GeV^2
            x_mod=x_mod*1.d+03
            x_real=x_mod*r
*     Calculate xsect error (absolute error)
*     Cross section error is same percent as ratio
            dx_real=x_mod*dr
                        
*     Check for NaN values
            if (isnan(x_real)) x_real = 0.0
            if (isnan(dx_real)) dx_real = -1000.0
            if (isnan(x_mod)) x_mod = 0.0
            if (isnan(eps_mod)) eps_mod = 0.0
            if (isnan(th_mod)) th_mod = 0.0
            if (isnan(phi)) phi = 0.0
            if (isnan(tt)) tt = 0.0
            if (isnan(tm)) tm = 0.0
            if (isnan(w)) w = 0.0
            if (isnan(q2)) q2 = 0.0            
            
            write(61,40) x_real,dx_real,x_mod,eps_mod,
     *           th_mod*180./3.14159,phi*180./3.14159,tm,w,q2
 40         format(3G15.5,f8.5,2f7.2,4f8.5)

            print *,""
            print *,"--------------"
            WRITE(*,*) 'phi (deg): ', phi*180./3.14159
            print *,"--------------"
            print *,'it',it
            print *,'nt',nt            
            print *,'ip',ip
            print *,'nphi',nphi
            print *,'ratio',r
            print *,'dratio',dr
            print *,"--------------"            
            print *,"xmodel inputs"
            print *,"--------------"
            print *,"pid: ", pid
            print *,"npol_set: ", npol_set
            print *,"Eb: ", Eb
            print *,"q2_set: ", q2_set
            print *,"w: ", w
            print *,"q2: ", q2
            print *,"tm: ", tm
            print *,"phi: ", phi
            print *,"eps_mod: ", eps_mod
            print *,"th_mod: ", th_mod
            print *,"x_mod: ", x_mod
            print *,"x_real: ", x_real
            print *,"dx_real: ", dx_real
            print *,"--------------"
            print *,""
            
         end do                 !phi

c        Write out kinematics for Henk.
         if(npol_set.gt.0) write(99,'(5f8.3,2x,2f6.2)')
     *   w,q2,eps_mod,th_mod*180./3.14159,tm,eps_set,q2_set

      end do                    !t

      close(51)
      close(52)
      close(61)
      close(71)
      print*,' '

      end

*=======================================================================

!     Dynamically construct and include
!     the model file based off PID and polarity
!     Fortran compiler will crash if files that
!     don't exist yet are added, so add files
!     as they are created.
      include 'models/xmodel_active.f'
      
*=======================================================================

      include 'eps_n_theta.f'
