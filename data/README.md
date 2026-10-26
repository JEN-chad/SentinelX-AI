# SentinelX AI - Dataset Samples & Documentation

This directory contains reference samples and synthetic network-flow data for offline replay and evaluation.

## Sample Files
- `samples/cic_ids2017_sample.csv`: Synthetic and representative flow records matching the CIC-IDS2017 schema with benign traffic, DoS-Slowloris attacks, and PortScan events.

## Downloading Full Datasets
For research experiments, download the official Canadian Institute for Cybersecurity (CIC) IDS 2017 dataset:
- URL: https://www.unb.ca/cic/datasets/ids-2017.html
- Recommended day: `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` and `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv`.

Place downloaded CSV files into this directory (ignored by Git) and use the `CICIDS2017Adapter` or `/api/v1/replay` endpoints.
