*=======================================================================
* xmodel for K^+ for KaonLT 2018-19
*=======================================================================      
      subroutine xmodel(pid,npol_set,Eb,q2_set,w_set,eps_set,
     *     w,q2,tm,phi,eps_mod,th_mod,x_mod,par_fn)

c     To calculate model cross-section, sigT+eps*sigL+ interfer._terms.

      implicit none

      character*2 prv_it
      common prv_it

      integer npol_set
      real Eb,q2_set,w_set,eps_set
      real w,q2,tm,phi
      real eps_mod,th_mod,x_mod

      real targ,mp,mn,pi
      real mpipl, mkpl
      parameter (pi=3.14159)
      parameter (mp=.93827231)   !mp
      parameter (mn=.93956563)   !mn
      parameter (mpipl=0.139570)
      parameter (mkpl=0.493677)
      
      real wfactor
      real thetacm

      integer i, test

      real sig,sigT,sigL,sigLT,sigTT
      real dsig,dsigT,dsigL,dsigLT,dsigTT

      character*80 par_fn
      character*2 pol
      character*4 pid

*     RLT (1/2/2024): Need to have 16 parameters (4 for L/T/LT/TT) for
*                     the xfit_in_t.py script to work. LT/TT are zeros
      real par(16)
      real p,e
      real f_tm,g_W,tav,f_tav

*     RLT (7/11/2024): Redefined functional forms of L, T, LT, TT
*                      that incorporates Q2-dep based of pi FF
      real Qdep_L, Qdep_T

      if(npol_set.lt.0) then
         pol='mn'
         targ=mn
      else
         pol='pl'
         targ=mp
      end if

      open(57, file=par_fn)
      do while (.true.)
         read(57, *, end=9) p, e, i
         par(i) = p
!     Print Statements
*         print *,"param: ", i, p, e
! You can customize the format as needed
      end do      
 9    close(57)      
      
*     Calculate model thetacm and epsilon at first.
      call eps_n_theta(pid,npol_set,Eb,w,q2,tm,
     *     thetacm,eps_mod)

*     Model sigL, sigT, sigTT, sigLT.

      tav=(0.0735 + 0.028*log(q2_set))*q2_set      
      f_tav=(abs(tm)-tav)/tav
      f_tm=abs(tm)/(abs(tm)+mpipl**2)**2 ! pole factor
      
**      
*     RLT (9/17/2024): Vijay's functions
      sigL=(par(1) + par(2)*log(q2_set))
     >     *exp((par(3)+par(4)*log(q2_set))*abs(tm))
      sigT=(par(5) + par(6)*log(q2_set))
     >     +((par(7)+par(8)*log(q2_set))*f_tav)
      sigLT=((par(9)/abs(tm))*exp((par(10)/abs(tm)))+(par(11)/abs(tm)))
     >     *sin(thetacm)
      sigTT=((par(13)/abs(tm)**3)*exp((par(14)*abs(tm)))
     >     +(par(15)/abs(tm)))*f_tm*sin(thetacm)**2
      
c     Correct for W.
      g_W=1./(W**2-targ**2)**2       ! W factor

      wfactor=g_W
      sigL=sigL*wfactor
      sigT=sigT*wfactor
      sigTT=sigTT*wfactor
      sigLT=sigLT*wfactor

** !! MODEL DEP STUDY !!
c      sigL=sigL*0.90-0.1
*     RLT (2/16/2024): Moved the unsep xsect down here so that the weight
*                      factor is included in calculation
      sig=sigT+eps_mod*sigL+eps_mod*cos(2.*phi)*sigTT
     >     +sqrt(2.0*eps_mod*(1.+eps_mod))*cos(phi)*sigLT

      sig=sig/2./pi/1.d+06      !dsig/dtdphicm in microbarns/MeV**2/rad
*     sig=sig/2./pi      !dsig/dtdphicm in microbarns/GeV**2/rad      

      x_mod=sig
      
      th_mod=thetacm
      
      end

*=======================================================================
