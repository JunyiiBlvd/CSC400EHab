import csv
import math

def calculate_stats(data):
    n = len(data)
    if n == 0:
        return 0, 0, 0
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std = math.sqrt(variance)
    
    # Lag-1 Autocorrelation
    if variance == 0:
        autocorr = 0
    else:
        num = sum((data[i] - mean) * (data[i+1] - mean) for i in range(n-1))
        autocorr = num / ((n-1) * variance)
    
    return mean, std, autocorr

def calculate_corr(data1, data2):
    n = len(data1)
    if n == 0:
        return 0
    mean1 = sum(data1) / n
    mean2 = sum(data2) / n
    
    num = sum((data1[i] - mean1) * (data2[i] - mean2) for i in range(n))
    den1 = sum((data1[i] - mean1) ** 2 for i in range(n))
    den2 = sum((data2[i] - mean2) ** 2 for i in range(n))
    
    if den1 == 0 or den2 == 0:
        return 0
    return num / math.sqrt(den1 * den2)

if __name__ == "__main__":
    with open('data/synthetic/normal_telemetry.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    variables = ['temperature', 'airflow', 'humidity', 'cpu_load']
    data = {var: [float(row[var]) for row in rows] for var in variables}
    
    print("| Variable    | Mean    | Std     | Lag-1 AutoCorr |")
    print("|-------------|---------|---------|----------------|")
    for var in variables:
        m, s, a = calculate_stats(data[var])
        print(f"| {var:<11} | {m:7.4f} | {s:7.4f} | {a:14.4f} |")

    # Correlation between airflow and cpu_load
    corr = calculate_corr(data['airflow'], data['cpu_load'])
    print(f"\nCorrelation between airflow and cpu_load: {corr:.4f}")
