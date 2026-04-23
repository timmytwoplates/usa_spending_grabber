# 🏛️ USAspending.gov Transaction Pro

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A high-performance desktop utility designed to interface with the [USAspending.gov API](https://api.usaspending.gov/). This tool allows researchers and analysts to fetch, filter, and export federal award transaction history with a focus on data visibility and modification tracking.

## ✨ Features

* **Multi-Threaded Fetching:** Utilizes `QThread` to ensure the UI remains responsive during heavy API calls.
* **Intelligent UI Grid:** Displays `Action Codes`, `Action Descriptions`, and `Obligations` in a searchable, sortable table.
* **Visual Auditing:** Automatically highlights non-modification ('M') records to quickly identify new awards or administrative changes.
* **Batch Processing:** Import contract IDs via CSV for mass data collection.
* **Export Ready:** One-click export of filtered results to a timestamped CSV.
* **Numeric Logic:** Custom sorting logic for financial columns to ensure accurate data analysis.

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* `pip install PyQt6 requests`

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/timmytwoplates/usa-spending-pro.git](https://github.com/timmytwoplates/usa-spending-pro.git)
