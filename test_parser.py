from analyze_pa_climate import parse_power

def test_monthly_precipitation_rate_conversion():
    payload = {'properties': {'parameter': {
        'T2M': {'202401': 3.0, '202402': 4.0, '202413': 5.0},
        'PRECTOTCORR': {'202401': 2.0, '202402': 1.0, '202413': 1.0}
    }}}
    d = parse_power(payload, 'test')
    assert len(d) == 2
    assert d.precipitation_mm.tolist() == [62.0, 29.0]

if __name__ == '__main__':
    test_monthly_precipitation_rate_conversion()
    print('Parser test passed')
