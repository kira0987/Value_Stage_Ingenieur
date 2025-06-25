import requests
import json

# List of indicators provided by the user
INDICATORS = [
    'NGDP_RPCH', 'PCPIPCH', 'BPBLTR', 'BPBLTL', 'GGR_NPGDP', 'GGR_G01', 'GGR_G02', 'GGR_G03', 'GGR_G04', 'GGR_G05',
    'LUR', 'UNR', 'UNR_NE', 'UNR_Y', 'IIP_AP', 'IIP_AI', 'IIP_A', 'IIP_L', 'FM_LBL', 'FM_L', 'NX_SH', 'CA_BAL',
    'GGS_BUDG', 'GGS_T01', 'GGS_T02', 'GGS_T03', 'GGS_T04', 'GGS_T05', 'LP', 'NX_GNP', 'NX_GDP', 'NX_NGDP', 'PI',
    'PCT_SM', 'PCT_SH', 'PCT_NGDP', 'PCT_GDP', 'PCT_LP', 'PCPIEPCH', 'PCPI', 'PCPIPCH', 'PGGDPCH', 'PGGDP',
    'PGDPCH', 'PGDP', 'LP_DPR', 'LP_MPR', 'LP_YPR', 'NX_NDP', 'NX_GDPD', 'NX_GDPR', 'NX_NDPD', 'NX_NGDPD',
    'NX_NDP_RPCH', 'NX_GDP_RPCH', 'NX_GDPR_PCH', 'NX_NGDP_RPCH'
]

def fetch_indicator_data(indicators, years, country_code="TUN"):
    indicators_str = ",".join(indicators)
    url = f"https://www.imf.org/external/datamapper/api/values={indicators_str}/{country_code}"
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0',
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"IMF API error: {response.status_code}")
    data = response.json()
    # Build a dictionary: {indicator: [{Year: ..., Value: ...}, ...]}
    indicator_results = {}
    for ind in indicators:
        indicator_results[ind] = []
        for year in years:
            try:
                value = data['values'][ind][country_code][str(year)]
            except Exception:
                value = None
            indicator_results[ind].append({"Year": year, "Value": value})
    return indicator_results

def main():
    try:
        indicators = INDICATORS
        print("Indicators:", indicators)
        years = list(range(2018, 2026))
        indicator_data = fetch_indicator_data(indicators, years)
        for ind, data in indicator_data.items():
            output_path = f"{ind}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {output_path}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()