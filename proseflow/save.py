# AUTOGENERATED! DO NOT EDIT! File to edit: save.ipynb (unless otherwise specified).

__all__ = ['save']

# Cell
import pandas as pd

# Cell
def save(resource, path, **kwargs):

    if isinstance(resource, pd.DataFrame):
        return resource.to_csv(path, index = False, header=True)
