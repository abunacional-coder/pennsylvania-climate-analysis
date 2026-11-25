"""Pennsylvania climate variability: reproducible exploratory NASA POWER analysis.

This script analyzes point-level monthly temperature and precipitation for four PA sites.
It is NOT a study of observed wildfire, actual forest health, or causal drivers.
"""
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
SITES = {
    'State College (Central)': (40.7934, -77.8600),
    'Pittsburgh (West)': (40.4406, -79.9959),
    'Scranton (Northeast)': (41.4090, -75.6624),
    'Harrisburg (Susquehanna)': (40.2732, -76.8867),
}
START, END = 2015, 2024
API = 'https://power.larc.nasa.gov/api/temporal/monthly/point'

def parse_power(payload, site):
    """Convert monthly POWER PRECTOTCORR rates (mm/day) to monthly totals."""
    try:
        params = payload['properties']['parameter']
        temperatures = params['T2M']
        precip_rates = params['PRECTOTCORR']
    except KeyError as exc:
        raise ValueError(f'NASA response missing a parameter: {exc}') from exc
    rows = []
    for key, temp in temperatures.items():
        if len(key) != 6 or not key.isdigit():
            continue
        if key[-2:] not in {f'{m:02d}' for m in range(1, 13)}:
            continue
        if key not in precip_rates:
            continue
        date = pd.to_datetime(key, format='%Y%m')
        rate = precip_rates[key]
        if temp is None or rate is None or float(temp) <= -900 or float(rate) <= -900:
            continue
        rows.append(dict(site=site, date=date, year=date.year, month=date.month,
                         temperature_c=float(temp), precipitation_mm=float(rate) * date.days_in_month))
    if not rows:
        raise ValueError(f'No valid monthly data for {site}')
    return pd.DataFrame(rows)

def get_site(site, lat, lon):
    response = requests.get(API, params={
        'parameters': 'T2M,PRECTOTCORR', 'community': 'AG',
        'longitude': lon, 'latitude': lat, 'format': 'JSON',
        'start': START, 'end': END,
    }, timeout=60)
    response.raise_for_status()
    data = response.json()
    if data.get('messages'):
        print(f'NASA message for {site}: {data["messages"]}')
    return parse_power(data, site)

def analyze(df):
    monthly_counts = df.groupby(['site', 'year']).month.nunique()
    if not (monthly_counts == 12).all() or len(monthly_counts) != len(SITES) * (END - START + 1):
        raise ValueError('Incomplete monthly coverage. Inspect downloaded data before comparison.')
    df = df.copy()
    thresholds = df.groupby('site').agg(
        warm_cutoff=('temperature_c', lambda s: s.quantile(0.75)),
        dry_cutoff=('precipitation_mm', lambda s: s.quantile(0.25)),
    )
    df = df.join(thresholds, on='site')
    df['warm_dry_month'] = ((df.temperature_c >= df.warm_cutoff) &
                            (df.precipitation_mm <= df.dry_cutoff))
    annual = df.groupby(['site', 'year'], as_index=False).agg(
        mean_temperature_c=('temperature_c', 'mean'),
        annual_precipitation_mm=('precipitation_mm', 'sum'),
        warm_dry_months=('warm_dry_month', 'sum'),
    )
    return df, annual

def plot_results(annual):
    for variable, ylabel, title, name in [
        ('mean_temperature_c', 'Annual mean temperature (°C)', 'Temperature by site', 'annual_temperature.png'),
        ('annual_precipitation_mm', 'Annual precipitation (mm)', 'Precipitation by site', 'annual_precipitation.png'),
        ('warm_dry_months', 'Warm–dry months per year (count)', 'Co-occurring warm and dry conditions', 'warm_dry_months.png'),
    ]:
        fig, ax = plt.subplots(figsize=(9, 5))
        for site, sub in annual.groupby('site'):
            ax.plot(sub.year, sub[variable], marker='o', label=site)
        ax.set(xlabel='Year', ylabel=ylabel, title=title)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(OUT / name, dpi=180)
        plt.close(fig)

def main():
    print('Downloading NASA POWER monthly data for four Pennsylvania locations...')
    df = pd.concat([get_site(site, *coords) for site, coords in SITES.items()], ignore_index=True)
    df, annual = analyze(df)
    df.to_csv(OUT / 'monthly_pa_climate.csv', index=False)
    annual.to_csv(OUT / 'annual_pa_climate.csv', index=False)
    plot_results(annual)
    print(f'Complete. Files saved to: {OUT}')
    print(annual.groupby('site')[['mean_temperature_c', 'annual_precipitation_mm', 'warm_dry_months']].mean().round(2))

if __name__ == '__main__':
    main()
