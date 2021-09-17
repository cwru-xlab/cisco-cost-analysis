# cost-analysis

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c597446cd6b6485dacec656dbc5609a8)](https://app.codacy.com/gh/project-cirrus/cost-analysis?utm_source=github.com&utm_medium=referral&utm_content=project-cirrus/cost-analysis&utm_campaign=Badge_Grade_Settings)

Calculators and analysis for determining the cost of cloud resources associated
with running Project Cirrus.

The `analysis` contains Jupyter notebooks that use the calculators in the
`calculators` package. The `TotalCostCalculator` in `total.py` is the top-level
calculator for specifying all system architecture parameters. All calculators
extend the `BaseCostCalculator` class in `base.py`.