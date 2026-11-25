"""Seasonal climatology from previously downloaded NASA POWER monthly data."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

results = Path(__file__).resolve().parent / 'results'
df = pd.read_csv(results / 'monthly_pa_climate.csv')
seasons = {12:'Winter',1:'Winter',2:'Winter',3:'Spring',4:'Spring',5:'Spring',6:'Summer',7:'Summer',8:'Summer',9:'Fall',10:'Fall',11:'Fall'}
df['season'] = df['month'].map(seasons)
order = ['Winter','Spring','Summer','Fall']
seasonal = df.groupby(['site','season'],as_index=False).agg(mean_temperature_c=('temperature_c','mean'), mean_monthly_precipitation_mm=('precipitation_mm','mean'))
seasonal.to_csv(results/'seasonal_climate_summary.csv',index=False)
for variable, title, ylabel, name in [
    ('mean_temperature_c','Seasonal Temperature Patterns in Pennsylvania (2015–2024)','Mean Temperature (°C)','seasonal_temperature.png'),
    ('mean_monthly_precipitation_mm','Seasonal Precipitation Patterns in Pennsylvania (2015–2024)','Mean Monthly Precipitation (mm)','seasonal_precipitation.png')]:
    plot_data = seasonal.pivot(index='season',columns='site',values=variable).reindex(order)
    ax = plot_data.plot(marker='o',figsize=(10,6))
    ax.set_title(title)
    ax.set_xlabel('Season')
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(results/name,dpi=300)
    plt.close()
print('Seasonal analysis completed successfully!')
print(seasonal.to_string(index=False))
