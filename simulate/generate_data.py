# generate_data.py
# Run normal operation simulation and save to CSV

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cstr_ode import simulate

t, y = simulate(t_span=(0, 500), n_points=1000)

df = pd.DataFrame({
    'time': t,
    # Tank 1
    'Ca1': y[0], 'Cb1': y[1], 'T1': y[2],
    # Tank 2
    'Ca2': y[3], 'Cb2': y[4], 'T2': y[5],
    # Tank 3
    'Ca3': y[6], 'Cb3': y[7], 'T3': y[8],
    # Label — normal operation
    'fault': 'none'
})

df.to_csv('data/normal_operation.csv', index=False)
print(f"Saved {len(df)} rows")
print(df.tail())

# ── Quick plot so you can see what happened ──
fig, axes = plt.subplots(2, 1, figsize=(12, 6))

axes[0].plot(t, y[2], label='T1'), axes[0].plot(t, y[5], label='T2')
axes[0].plot(t, y[8], label='T3')
axes[0].set_ylabel('Temperature [K]'), axes[0].legend(), axes[0].set_title('Tank Temperatures')

axes[1].plot(t, y[0], label='Ca1'), axes[1].plot(t, y[3], label='Ca2')
axes[1].plot(t, y[6], label='Ca3')
axes[1].set_ylabel('Concentration A [mol/m³]'), axes[1].legend()
axes[1].set_title('Reactant A Concentration')

plt.tight_layout()
plt.savefig('data/normal_operation_plot.png', dpi=150)
plt.show()