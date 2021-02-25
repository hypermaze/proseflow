# AUTOGENERATED! DO NOT EDIT! File to edit: utils.ipynb (unless otherwise specified).

__all__ = ['merge_csv_in_dir', 'tree_select_kv', 'deep_path_from_keysequence', 'get_paths', 'show_tabs', 'take_while',
           'partition', 'partition_all', 'create_embedding_files_for_visualization', 'pipe', 'dedupe_conseq']

# Cell
from typing import List
from fastcore.basics import typed
from fastcore.test import *
from toolz import thread_first, thread_last
import proseflow.text as txt

from functools import reduce
from typing import Iterable, List, Union

from pydash import get
from typeguard import typechecked

# Cell

import os
import pandas as pd
from itertools import product
import argparse
import sys

def merge_csv_in_dir(dir_path):
    for dirpath, _, fnames in os.walk(dir_path):
        fpaths = (["/".join(t) for t in [*product([dirpath], fnames)]])
        dfs = [pd.read_csv(fpath) for fpath in fpaths]

        print(dfs[0].columns)
        pd.concat(dfs).to_csv("merged.csv", index = False, header=True)

# Cell

# TODO: [Markus] : Walk or Tree-seq implementation
# @typechecked
def tree_select_kv(data, paths, keys_wanted):
    flat_dict = {}
    for path in paths:
        # for keyseq in path:
        # print(keyseq)
        # print(path, keyseq)
        leaf_key = None
        if path[-1:]:
            leaf_key = path[-1:][0]

        # print(path, leaf_key)
        if leaf_key in keys_wanted:
            deep_dot_path = deep_path_from_keysequence(path)
            # print(deep_dot_path, keyseq, leaf_key)
            value = get(data, deep_dot_path)
            key = leaf_key
            flat_dict[key] = value
    return flat_dict


@typechecked
def deep_path_from_keysequence(keysequence: list) -> str:
    return reduce(lambda path, part: path + "." + str(part), keysequence, "")


def get_paths(d: dict) -> Iterable[str]:
    """Given a dict, it returns an array with all paths
    Example return: ['PubmedArticle', 0, 'MedlineCitation']
    """
    q = [(d, [])]
    while q:
        n, p = q.pop(0)
        yield p
        if isinstance(n, dict):
            for k, v in n.items():
                q.append((v, p + [k]))
        elif isinstance(n, list):
            for i, v in enumerate(n):
                q.append((v, p + [i]))

# Cell
from tabulate import tabulate
def show_tabs(doc):
    print(tabulate([
            [token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
            token.shape_, token.is_alpha, token.is_stop]
            for token in doc], headers=["token", "lemma", "POS", "Tag", "DEP", "shape", "is_alpha", "is_stop"]
  ))

# Cell
def take_while(fn, coll):
    """Yield values from coll until fn is False"""
    for e in coll:
        if fn(e):
            yield e
        else:
            return

def partition(n, coll, step=None):
    return take_while(lambda e: len(e) == n,
        (coll[i:i+n] for i in range(0, len(coll), step or n)))

def partition_all(n, coll, step=None):
    return (coll[i:i+n] for i in range(0, len(coll), step or n))

[*partition(2, [1, 2,3 ,4,5, 5,6,7], 1)]

# Cell
@typed
def create_embedding_files_for_visualization(metadata, vectors, metadata_headers=None):
    """ Create embedding files for visualization. Sentences can be any kind of metadata """
    metadata = [*metadata]
    assert len(metadata) == len(vectors)

    vectors_filepath = f"/results/vectors.tsv"
    metadata_filepath = f"results/metadata.tsv"

    out_vectors = open(vectors_filepath, "w", encoding="utf-8")
    out_metadata = open(metadata_filepath, "w", encoding="utf-8")

    # Meta File Header
    if metadata_headers:
        out_metadata.write("\t".join(metadata_headers) + "\n")

    for i in range(len(vectors)):
        out_metadata.write("\t".join(metadata[i]) + "\n")
        out_vectors.write("\t".join([str(x) for x in vectors[i]]) + "\n")

    out_vectors.close()
    out_metadata.close()

# Cell
def pipe(*funcs:List[callable], thread="first"):
    thread = thread_first if thread == "first" else thread_last
    return lambda data: thread(data, *funcs)

# Cell
def dedupe_conseq(coll):
    """
    Returns a generator of the elements of coll with consecutive duplicates removed.
    """
    initial = True
    prev = None
    for e in coll:
        if initial or e != prev:
            initial = False
            yield e
        prev = e