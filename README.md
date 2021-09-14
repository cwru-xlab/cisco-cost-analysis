# cost-analysis

Calculators and analysis for determining the cost of cloud resources associated
with running Project Cirrus.

The `analysis` contains Jupyter notebooks that use the calculators in the
`calculators` package. The `TotalCostCalculator` in `total.py` is the top-level
calculator for specifying all system architecture parameters. All calculators
extend the `BaseCostCalculator` class in `base.py`.