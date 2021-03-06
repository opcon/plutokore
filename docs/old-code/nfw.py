
# coding: utf-8

# In[1]:

import numpy as np
import astropy.units as u
import astropy.constants as const
import astropy.cosmology as cosmology
import scipy.integrate as integrate
from tabulate import tabulate
class NFW_Profile:
    
    def __init__(self, halo_mass, redshift, T=None, delta_vir=None, mu=None, f_gas=None, omega_b=None, gamma=None, concentration_method=None,
                cosmo=None):
        """Creates an NFW profile for the given halo mass and redshift"""
        
        
        self.halo_mass = halo_mass
        self.redshift = redshift
        
        if delta_vir is None:
            delta_vir = 200
        self.delta_vir = delta_vir
        
        
        if mu is None:
            mu = 0.6
        self.mu = mu
        
        if f_gas is None:
            f_gas = 1.0
        self.f_gas = f_gas
        
        if cosmo is None:
            cosmo = cosmology.Planck15
        self.cosmo = cosmo
        
        if omega_b is None:
            omega_b = self.cosmo.Ob(self.redshift) / self.cosmo.Om(self.redshift)
        self.omega_b = omega_b
        
        if gamma is None:
            gamma = 5.0 / 3.0
        self.gamma = gamma
        
        if concentration_method is None:
            concentration_method = 'klypin'
            
        self.critical_density = self.calculate_critical_density(self.redshift, cosmo=self.cosmo)
        self.virial_radius = self.calculate_virial_radius(self.halo_mass, self.delta_vir, self.critical_density)
        
        if T is None:
            T = self.calculate_temperature(self.halo_mass, self.mu, self.virial_radius)
        self.T = T
        
        self.concentration = self.calculate_concentration(self.halo_mass, redshift=self.redshift, method=concentration_method, cosmo=self.cosmo)
        self.scale_radius = self.calculate_scale_radius(self.virial_radius, self.concentration)
        self.characteristic_density = self.calculate_characteristic_density(self.delta_vir, self.concentration)
        self.nfw_parameter = self.calculate_nfw_parameter(self.scale_radius, self.characteristic_density, self.critical_density, 
                                                          self.mu, self.T)
        self.phi_nfw = self.calculate_phi_nfw(self.nfw_parameter, self.mu, self.T)
        self.central_density = self.calculate_central_density(self.f_gas, self.omega_b, self.halo_mass, 
                                                              self.virial_radius, self.nfw_parameter, self.scale_radius)
        self.sound_speed = self.calculate_sound_speed(self.gamma, self.T, self.mu)
        
    def get_density(self, radius):
        """Calculates the density for this profile at the specified radius"""
        return self.calculate_density_at_radius(self.central_density, self.nfw_parameter, self.scale_radius, radius)
        
    @staticmethod
    def calculate_temperature(halo_mass, mu, virial_radius, gamma_isothermal=1.5):
        """Calculates the virial temperature using an isothermal approximation from Makino+98"""
        t_vir = (gamma_isothermal/3.0) * (mu * const.m_p) * (const.G * halo_mass) / (virial_radius)
        return t_vir.to(u.keV)
        
    @staticmethod
    def calculate_critical_density(redshift, cosmo=cosmology.Planck15):
        """Calculates the critical density parameter for the given redshift,
        using the Planck (15) survey results for the hubble constant"""
        H_squared = cosmo.H(redshift) ** 2
        critical_density = (3.0 * H_squared) / (8.0 * np.pi * const.G)
        return critical_density.to(u.g / u.cm ** 3)
    
    @staticmethod
    def calculate_virial_radius(virial_mass, delta_vir, critical_density):
        """Calculates the virial radius for the given virial mass, delta_vir and critical density"""
        r_vir = ((3.0 * virial_mass)/(4.0 * np.pi * delta_vir * critical_density)) ** (1.0/3.0)
        return r_vir.to(u.kpc)
    
    @staticmethod
    def calculate_concentration(virial_mass, method = 'bullock', redshift = 0, cosmo=cosmology.Planck15):
        """Calculates the concentration parameter for a given virial mass and redshift"""
        # parameters for Dolag+04, delta_vir is 200 using MEAN density. Cosmology closely matches WMAP9
        c_0_dolag = 9.59
        alpha_dolag = -0.102
        
        # parameters for Klypin+16 Planck, all halos, delta_vir is 200 using critical density
        c_0_klypin_planck_all = 7.40
        gamma_klypin_planck_all = 0.120
        m_0_klypin_planck_all = 5.5e5
        
        # parameters for Klypin+16 Planck, relaxed halos, delta_vir is 200 using critical density
        c_0_klypin_planck_relaxed = 7.75
        gamma_klypin_planck_relaxed = 0.100
        m_0_klypin_planck_relaxed = 4.5e5
        
        # parameters for Klypin WMAP7 all halos, delta_vir is 200 using critical density
        c_0_wmap_all = 6.60
        gam_wmap_all = 0.110
        m_0_wmap_all = 2e6
        
        # parameters for Klypin WMAP7 relaxed halos, delta_vir is 200 using critical density
        c_0_wmap_relaxed = 6.90
        gam_wmap_relaxed = 0.090
        m_0_wmap_relaxed = 5.5e5
        
        # parameters for Dutton+14, NFW model, delta_vir = 200 using critical density, Planck cosmology
        b_dutton = -0.101 + 0.026 * redshift
        a_dutton = 0.520 + (0.905 - 0.520) * np.exp(-0.617 * (redshift ** 1.21))
        
        # parameters for Maccio+08, NFW model, WMAP5, delta_vir = 200 using critical density
        zero_maccio = 0.787
        slope_maccio = -0.110
        
        
        c = 0.0
        
        # Dolag+04 method
        if method == 'dolag':
            c = (c_0_dolag)/(1 + redshift) * ((virial_mass / (10.0 ** 14 * u.M_sun * (1.0/cosmo.h))) ** alpha_dolag)
        # Bullock+01 method, cosmological parameters agree with WMAP9, delta_vir = 180 using 337 using mean density (for LambdaCDM)
        elif method == 'bullock':
            c = (8.0/(1+redshift)) * (10 ** ((-0.13)*(np.log10(virial_mass.to(u.M_sun).value)-14.15)))
        # Klypin+16 methods
        elif method == 'klypin-planck-all':
            c = (c_0_klypin_planck_all * ((virial_mass / (1e12 * u.M_sun * (cosmo.h ** (-1)))) ** -gamma_klypin_planck_all) * 
                 (1 + (virial_mass / (m_0_klypin_planck_all * (1e12 * u.M_sun * (cosmo.h ** (-1))))) ** 0.4))
        elif method == 'klypin-planck-relaxed':
            c = (c_0_klypin_planck_relaxed * ((virial_mass / (1e12 * u.M_sun * (cosmo.h ** (-1)))) ** -gamma_klypin_planck_relaxed) * 
                 (1 + (virial_mass / (m_0_klypin_planck_relaxed * (1e12 * u.M_sun * (cosmo.h ** (-1))))) ** 0.4))
        elif method == 'klypin-wmap-all':
            c = ((c_0_wmap_all * ((virial_mass / (1e12 * u.M_sun * (cosmo.h ** (-1)))) ** -gam_wmap_all)) *
            ((1 + (virial_mass / (m_0_wmap_all * (1e12 * u.M_sun * (cosmo.h ** (-1))))) ** 0.4)))
        elif method == 'klypin-wmap-relaxed':
            c = ((c_0_wmap_relaxed * ((virial_mass / (1e12 * u.M_sun * (cosmo.h ** (-1)))) ** -gam_wmap_relaxed)) *
            ((1 + (virial_mass / (m_0_wmap_relaxed * (1e12 * u.M_sun * (cosmo.h ** (-1))))) ** 0.4)))
        # Dutton+14 method
        elif method == 'dutton':
            logc = a_dutton + b_dutton * np.log10(virial_mass / (1e12 * (cosmo.h ** -1) * u.M_sun))
            c = 10 ** logc
        # Maccio+08 method
        elif method == 'maccio':
            logc = zero_maccio + slope_maccio * (np.log10(virial_mass / (u.M_sun * (1.0/cosmo.h))) - 12)
            c = 10 ** logc
        return c
    
    @staticmethod
    def calculate_scale_radius(virial_radius, concentration):
        """Calculates the scale radius for a given virial radius and concentration"""
        r_s = virial_radius / concentration
        return r_s
    
    @staticmethod
    def calculate_characteristic_density(delta_vir, concentration):
        """Calculates the characteristic density for a given Delta_vir and concentration"""
        char_density = (delta_vir / 3.0) * ((concentration ** 3.0) / (np.log(1.0 + concentration) - (concentration / (1.0 + concentration))))
        return char_density
    
    @staticmethod
    def calculate_nfw_parameter(r_s, char_density, rho_crit, mu, T):
        """Calculates the nfw parameter for a given scale radius, characteristic density, critical density, mean molecular weight
        and temperature (in keV)"""
        delta_nfw = const.G * 4 * np.pi * char_density * rho_crit * (r_s ** 2.0) * (mu * const.m_p) / T
        return delta_nfw.si
    
    @staticmethod
    def calculate_phi_nfw(delta_nfw, mu, T):
        """Calculates phi NFW for a given NFW parameter, mean molecular weight and temperature"""
        phi_nfw = -delta_nfw * (T / (mu * const.m_p))
        return phi_nfw.si
    
    @staticmethod
    def calculate_central_density(f_gas, omega_b, virial_mass, virial_radius, delta_nfw, r_s):
        """Calculates the central density for the NFW profile, given the hot gas fraction, baryonic matter percentage and
        virial mass of the halo"""
        integral = (u.kpc ** 3 ) * integrate.quad(lambda r: 4*np.pi*(r**2) * np.exp(-delta_nfw)*np.power((1.0+r/r_s.value), delta_nfw / (r / r_s.value)), 0, virial_radius.value)
        denom = integral[0]
        rho_0 = (f_gas * omega_b * virial_mass) / denom
        return rho_0.to(u.g * u.cm ** (-3))
    
    @staticmethod
    def calculate_sound_speed(gamma, T, mu):
        return np.sqrt((gamma * T)/(mu * const.m_p)).to(u.km / u.s)
    
    @staticmethod
    def calculate_density_at_radius(central_density, delta_nfw, r_s, r):
        return central_density * np.exp(-delta_nfw)*(1+r/r_s) ** (delta_nfw/(r/r_s))
    
    #NFW helper methods
    @staticmethod
    def GetDensityAtPoint(rho_0,delta,r_s,r):
        return calculate_density_at_radius(rho_0, delta, r_s, r)
    @staticmethod
    def CalculateSoundSpeed(gamma, k_BT, mu, m_p):
        return calculate_sound_speed(gamma, k_BT, mu)


# In[16]:

NFW_Profile.calculate_concentration(1e12 * u.M_sun, method='klypin-wmap-all', redshift=0, cosmo=cosmology.Planck15)


# In[ ]:



