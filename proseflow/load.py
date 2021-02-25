# AUTOGENERATED! DO NOT EDIT! File to edit: load.ipynb (unless otherwise specified).

__all__ = ['load', 'load', 'load', 'load']

# Cell
import json
import os
import re
from collections.abc import Iterable
from io import BytesIO
from typing import Dict

import gspread
import pandas as pd
import requests
import spacy
import stanza
from dotenv import load_dotenv
from multipledispatch import dispatch
from pandas import DataFrame
from sentence_transformers import SentenceTransformer, models
from spacy_stanza import StanzaLanguage
from textacy.corpus import Corpus
from typeguard import typechecked

from .spec import *

# Cell
# Example: https://docs.google.com/spreadsheets/d/1N_aANmDaosjAlodJ5nMNVPfe6REsDtsNYHj_ltH3Q_0/edit?usp=drive_web&ouid=112317186249575590696
#export
@typechecked
def _load_gsheet(
    url: str,
    sheet_number: int = 0,
    credential_path: str = os.getenv("GSHEET_CREDENTIALS"),
    **kwargs,
) -> GSHEET:
    if not credential_path:
        raise Exception("Add the $GSHEET_CREDENTIALS variable to your .env file.")
    gc = gspread.service_account(filename=credential_path)
    wb = gc.open_by_url(url)
    worksheet = wb.get_worksheet(sheet_number)

    return worksheet

# Cell
def _load_corpus(nlp, path):
    corpus = Corpus(nlp).load(nlp, path)
    for label in labels:
        nlp.vocab.strings.add(label)

    return corpus

# Cell
#export
@dispatch((spacy.language.Language, StanzaLanguage), str)
def load(nlp, path):
    return _load_corpus(nlp, path)

# Cell
@dispatch(Iterable)
def load(resource, **kwargs):
    """All shapes become lists for further processing
    #TODO: [Rico] -- a job for autoconvert?
    """
    shape_iterable = convert(resource, source=type(resource), target=list)
    return load(shape_iterable, **kwargs)

# Cell
#export
@dispatch(list)
def load(resource, **kwargs):
    #! checks the type of the FIRST element (like an actual pmid, not a list of pmids)
    shape = kwargs.get("input_type") or infer_type(resource[0])
    if shape == PUBMED_IDS:
        content = kwargs.get(PUBMED_CONTENT) or "ALL"
        if content == "ABSTRACT":
            return _get_pubmed_abstracts(pmids=resource)
        if content == "INFO":
            return _get_pubmed_info(pmids=resource)
        return _get_pubmed_records(pmids=resource)

    return None

# Cell
def _load_transformer(model_name):
    # ! TODO: abstract so that it also works for Tensorflow, etc..; right now its only PyTorch
    # TODO: make sure it actually loads a huggingface transformer and not the sentence transformer version
    model_name = model_name.split(":")[1]

    return models.Transformer(model_name)

# Cell
def _load_spacy(model_name: str = "en_core_web_sm", **kwargs) -> spacy.language.Language:
    print("Loading SpaCy...")
    try:
        nlp = spacy.load(model_name, **kwargs)
    except OSError:
        try:
            spacy.cli.download(model_name)
            nlp = spacy.load(model_name, **kwargs)
        except:
            print("Download the SpaCy model before trying to import it.")
            return None
    return nlp

# Cell
def _load_stanza(
    stanza_setup: Dict[str, str] = {
        "lang": "en",
        "package": "genia",
        "processors": {"ner": "bionlp13cg"},
    },
    use_gpu: bool = True,
) -> stanza.Pipeline:
    # TODO: [RICO -> put use_gpu inside one config]
    print("loading stanza", stanza_setup)
    try:
        snlp = stanza.Pipeline(**stanza_setup, use_gpu=use_gpu)
    except:
        stanza.download(**stanza_setup)
        snlp = stanza.Pipeline(**stanza_setup, use_gpu=use_gpu)

    return snlp

# Cell
@dispatch(str)  # dispatch decides if the load gets executed; the type level is more expressive
def load(resource, *args, **kwargs):
    """This names the important args like config and credentials, but leaves options open"""


    if resource.endswith(".csv"):
        return pd.read_csv(resource)
    if resource.endswith(".tsv"):
        pass
    if resource == "some url":
        pass  # scrape (params:)
    if resource.endswith(".json"):
        return _load_json(resource)
    if resource.endswith(".txt"):
        return _load_txt(resource)

    shape = kwargs.get("input_type") or infer_type(resource)
    print(shape, "shape", kwargs)
    as_type = kwargs.get("as_type")
    should_convert = as_type is not None
    if shape == GSHEET:
        gs = _load_gsheet(resource, **kwargs)

        # ! Don't Try to be smart here and use (should_convert and convert(...) -- there's problems with boolean
        # operators and some types)
        if should_convert:
            gs = convert(gs, source=GSHEET, target=as_type)
            if as_type == DataFrame and kwargs.get("columns"):
                gs = gs[kwargs.get("columns")]
        return gs
    if shape == SPACY_MODEL:
        return _load_spacy(resource, **kwargs)
    if shape == STANZA_MODEL:
        if as_type:
            kwargs.pop("as_type")
        snlp = _load_stanza(**kwargs)
        if as_type:
            return convert(snlp, source=STANZA_MODEL, target=SPACY_MODEL)
        return snlp
    if shape == SENTENCE_TRANSFORMER:
        return SentenceTransformer(resource)
    if shape == TRANSFORMER:
        transformer_model = _load_transformer(resource)
        if as_type:
            return convert(
                transformer_model, source=TRANSFORMER, target=SENTENCE_TRANSFORMER
            )
        return transformer_model

    return "None found"