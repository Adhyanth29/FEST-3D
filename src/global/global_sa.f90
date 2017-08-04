module global_sa

  real, parameter  :: cb1    = 0.1355
  real, parameter  :: cb2    = 0.6220
  real, parameter  :: cw2    = 0.3
  real, parameter  :: cw3    = 2.0
  real, parameter  :: cv1    = 7.1
  real, parameter  :: ct3    = 1.2
  real, parameter  :: ct4    = 0.5
  real, parameter  :: sigma  = 2./3.
  real, parameter  :: kappa  = 0.41

  real, parameter  :: cw1    = (cb1/(kappa**2)) + ((1+cb2)/sigma)

end module global_sa