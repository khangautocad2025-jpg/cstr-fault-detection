# cstr_ode.py
# CSTR Series Simulator — Ethylene → Ethylene Oxide → Ethylene Glycol
# Reaction: A → B → C (exothermic, 3 tanks in series)
# Your job: read every comment and make sure you can explain each line

import numpy as np
from scipy.integrate import solve_ivp

# ─── Kinetic & Physical Parameters ───────────────────────────────────────────
# Arrhenius: k(T) = A * exp(-Ea / R*T)
# These are based on simplified EO synthesis literature values

R       = 8.314        # J/mol·K — universal gas constant (you should know this)

# Reaction 1: A → B (Ethylene → Ethylene Oxide)
A1      = 1.0e10       # pre-exponential factor [1/s]
Ea1     = 75000        # activation energy [J/mol]
dHr1    = -105000      # heat of reaction [J/mol], negative = exothermic

# Reaction 2: B → C (Ethylene Oxide → Ethylene Glycol)
A2      = 2.0e8
Ea2     = 65000
dHr2    = -80000       # also exothermic

# Physical properties (assumed constant — simplification for year 1)
rho     = 900          # fluid density [kg/m³]
Cp      = 3500         # heat capacity [J/kg·K]
U       = 800          # heat transfer coefficient [W/m²·K]
Area    = 2.0          # heat transfer area per tank [m²]

# ─── CSTR Design Parameters ───────────────────────────────────────────────────
V       = 1.0          # volume of each tank [m³]  ← τ = V/v0
v0      = 0.05         # volumetric flow rate [m³/s]
tau     = V / v0       # residence time [s] — YOUR formula from homework

# Coolant
Tc      = 320.0        # coolant temperature [K] — same for all 3 tanks (normal)

# ─── Inlet Feed Conditions ────────────────────────────────────────────────────
Ca_feed = 2.0          # concentration of A entering tank 1 [mol/m³]
Cb_feed = 0.0          # no B in the feed
T_feed  = 340.0        # feed temperature [K]


def arrhenius(A, Ea, T):
    """
    Arrhenius rate constant.
    k = A * exp(-Ea / R*T)
    Higher T → higher k → faster reaction → more heat → higher T (runaway risk!)
    """
    return A * np.exp(-Ea / (R * T))


def cstr_series_odes(t, y, Tc_tanks):
    """
    ODEs for 3 CSTRs in series.

    State vector y = [Ca1, Cb1, T1, Ca2, Cb2, T2, Ca3, Cb3, T3]
    
    For each tank i, the mass and energy balances are:
    
    Mass balance on A:  dCa/dt = (Ca_in - Ca) / tau  -  k1(T)*Ca
    Mass balance on B:  dCb/dt = (Cb_in - Cb) / tau  +  k1(T)*Ca  -  k2(T)*Cb
    Energy balance:     dT/dt  = (T_in - T) / tau
                                 - (dHr1 * k1(T)*Ca + dHr2 * k2(T)*Cb) / (rho*Cp)
                                 - U*Area*(T - Tc) / (rho*Cp*V)

    Tc_tanks: list of coolant temps [Tc1, Tc2, Tc3] — lets us simulate coolant failure per tank
    """
    Ca1, Cb1, T1, Ca2, Cb2, T2, Ca3, Cb3, T3 = y
    Tc1, Tc2, Tc3 = Tc_tanks

    # ── Tank 1 ── inlet = feed
    k1_1 = arrhenius(A1, Ea1, T1)
    k2_1 = arrhenius(A2, Ea2, T1)
    dCa1 = (Ca_feed - Ca1) / tau  -  k1_1 * Ca1
    dCb1 = (Cb_feed - Cb1) / tau  +  k1_1 * Ca1  -  k2_1 * Cb1
    dT1  = ((T_feed - T1) / tau
            - (dHr1 * k1_1 * Ca1 + dHr2 * k2_1 * Cb1) / (rho * Cp)
            - U * Area * (T1 - Tc1) / (rho * Cp * V))

    # ── Tank 2 ── inlet = outlet of tank 1
    k1_2 = arrhenius(A1, Ea1, T2)
    k2_2 = arrhenius(A2, Ea2, T2)
    dCa2 = (Ca1 - Ca2) / tau  -  k1_2 * Ca2
    dCb2 = (Cb1 - Cb2) / tau  +  k1_2 * Ca2  -  k2_2 * Cb2
    dT2  = ((T1 - T2) / tau
            - (dHr1 * k1_2 * Ca2 + dHr2 * k2_2 * Cb2) / (rho * Cp)
            - U * Area * (T2 - Tc2) / (rho * Cp * V))

    # ── Tank 3 ── inlet = outlet of tank 2
    k1_3 = arrhenius(A1, Ea1, T3)
    k2_3 = arrhenius(A2, Ea2, T3)
    dCa3 = (Ca2 - Ca3) / tau  -  k1_3 * Ca3
    dCb3 = (Cb2 - Cb3) / tau  +  k1_3 * Ca3  -  k2_3 * Cb3
    dT3  = ((T2 - T3) / tau
            - (dHr1 * k1_3 * Ca3 + dHr2 * k2_3 * Cb3) / (rho * Cp)
            - U * Area * (T3 - Tc3) / (rho * Cp * V))

    return [dCa1, dCb1, dT1, dCa2, dCb2, dT2, dCa3, dCb3, dT3]


def simulate(t_span=(0, 500), n_points=1000, Tc_tanks=None):
    """
    Run the simulation under normal operating conditions.
    Returns time array and state matrix.
    """
    if Tc_tanks is None:
        Tc_tanks = [Tc, Tc, Tc]   # normal: all coolants working

    # Initial conditions — start near feed conditions
    y0 = [Ca_feed, 0.0, T_feed,
          Ca_feed, 0.0, T_feed,
          Ca_feed, 0.0, T_feed]

    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    sol = solve_ivp(
        fun=lambda t, y: cstr_series_odes(t, y, Tc_tanks),
        t_span=t_span,
        y0=y0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-6
    )

    return sol.t, sol.y