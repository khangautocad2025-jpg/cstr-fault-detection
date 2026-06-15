# fault_injector.py
# Injects 3 fault types into the CSTR series simulation
# Each fault starts at t=200s — system is at steady state by then

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

# ── Same parameters as cstr_ode.py ───────────────────────────────────────────
R    = 8.314
A1, Ea1, dHr1 = 1.0e10, 75000, -105000
A2, Ea2, dHr2 = 2.0e8,  65000,  -80000
rho, Cp       = 900, 3500
U, Area       = 800, 2.0
V             = 1.0
Tc_normal     = 320.0
Ca_feed_normal = 2.0
T_feed        = 340.0

def arrhenius(A, Ea, T):
    return A * np.exp(-Ea / (R * T))

def cstr_odes(t, y, v0, Ca_feed, Tc_tanks):
    """Same ODE as cstr_ode.py but v0 and Ca_feed are now parameters
    so we can change them mid-simulation to inject faults"""
    tau = V / v0
    Ca1, Cb1, T1, Ca2, Cb2, T2, Ca3, Cb3, T3 = y
    Tc1, Tc2, Tc3 = Tc_tanks

    def tank(Ca_in, Cb_in, T_in, Ca, Cb, T, Tc):
        k1 = arrhenius(A1, Ea1, T)
        k2 = arrhenius(A2, Ea2, T)
        dCa = (Ca_in - Ca) / tau - k1 * Ca
        dCb = (Cb_in - Cb) / tau + k1 * Ca - k2 * Cb
        dT  = ((T_in - T) / tau
               - (dHr1 * k1 * Ca + dHr2 * k2 * Cb) / (rho * Cp)
               - U * Area * (T - Tc) / (rho * Cp * V))
        return dCa, dCb, dT

    d1 = tank(Ca_feed, 0.0,  T_feed, Ca1, Cb1, T1, Tc1)
    d2 = tank(Ca1,     Cb1,  T1,     Ca2, Cb2, T2, Tc2)
    d3 = tank(Ca2,     Cb2,  T2,     Ca3, Cb3, T3, Tc3)

    return [*d1, *d2, *d3]


def run_fault_simulation(fault_type, t_fault=200, t_end=500, n_points=1000):
    """
    Run simulation where fault is injected at t=t_fault.
    
    Phase 1: normal operation (0 to t_fault)
    Phase 2: fault active   (t_fault to t_end)
    """

    # ── Steady state from normal run (use as initial condition) ──
    y0 = [1.252, 0.498, 339.84,   # tank 1 steady state values
          0.812, 0.623, 339.68,   # tank 2
          0.501, 0.687, 339.49]   # tank 3

    # ── Phase 1: normal (0 → t_fault) ────────────────────────────
    t1_eval = np.linspace(0, t_fault, n_points // 2)
    sol1 = solve_ivp(
        fun=lambda t, y: cstr_odes(t, y, V/20, Ca_feed_normal, [Tc_normal]*3),
        t_span=(0, t_fault), y0=y0, t_eval=t1_eval, method='RK45', rtol=1e-6
    )

    # ── Set fault parameters ──────────────────────────────────────
    if fault_type == 'coolant_failure':
        # Tc in tank 1 jumps to 380K (was 320K) — coolant stops working
        v0_f       = V / 20
        Ca_feed_f  = Ca_feed_normal
        Tc_f       = [380.0, Tc_normal, Tc_normal]

    elif fault_type == 'feed_spike':
        # Feed concentration doubles suddenly
        v0_f       = V / 20
        Ca_feed_f  = Ca_feed_normal * 2
        Tc_f       = [Tc_normal] * 3

    elif fault_type == 'flow_drop':
        # Flow rate drops by 50% → residence time doubles
        v0_f       = (V / 20) * 0.5
        Ca_feed_f  = Ca_feed_normal
        Tc_f       = [Tc_normal] * 3

    # ── Phase 2: fault active (t_fault → t_end) ──────────────────
    y_fault_start = sol1.y[:, -1]   # pick up where phase 1 ended
    t2_eval = np.linspace(t_fault, t_end, n_points // 2)
    sol2 = solve_ivp(
        fun=lambda t, y: cstr_odes(t, y, v0_f, Ca_feed_f, Tc_f),
        t_span=(t_fault, t_end), y0=y_fault_start,
        t_eval=t2_eval, method='RK45', rtol=1e-6
    )

    # ── Combine both phases ───────────────────────────────────────
    t_all = np.concatenate([sol1.t, sol2.t])
    y_all = np.concatenate([sol1.y, sol2.y], axis=1)

    labels = (['none'] * len(sol1.t)) + ([fault_type] * len(sol2.t))

    return t_all, y_all, labels