# AUTOGENERATED! DO NOT EDIT! File to edit: text.ipynb (unless otherwise specified).

__all__ = ['STRING_FUNCS', 'text_to_vector', 'create_index', 'query_index', 'ents_w_candidates', 'candidates_lables',
           'get_ent_from_token', 'load_sci_pipe', 'm_reannotate', 'last_token_of_entity', 'negated_ents',
           'show_negex_entities', 'get_token_and_entities_as_spans', 'add_pipes_mutative', 'rsetattr', 'rgetattr',
           'get_entity_diff', 'merge_named_entities', 'print_table', 'show_noun_chunks', 'doc_has_entity_labels',
           'get_merged_docs_for_texts', 'get_tokenidx_for_char', 'extract_named_entities_info', 'pattern_vis',
           'prep_pattern', 'add_matches', 'get_lemma', 'check_for_non_trees', 'annotate_NER', 'construct_pattern_old',
           'construct_pattern', 'match_texts']

# Cell
from fastcore.basics import listify
import faiss
from typing import List

# Cell
STRING_FUNCS = ["capitalize", "count", "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isidentifier", "islower",
                "isnumeric", "isspace", "istitle", "isupper", "lower", "lstrip", "replace", "rstrip", "split", "strip", "upper"]

# Cell
# TODO: add convert so that i automatically converts a string/np array/dataframe/tensor into a list
def text_to_vector(text_form, embedder):
    embeddings = embedder.encode(text_form, convert_to_tensor=True)
    return embeddings.cpu().detach().numpy()

# Cell
def create_index(vectors):
    faiss_index = faiss.IndexFlatL2(len(vectors[0]))
    faiss_index.add(vectors)

#     print(faiss_index.ntotal)

    return faiss_index

# Cell
def query_index(text, embedder, target_list, index, with_distance=False, k=10):
    embedding = embedder.encode([text])
    distances, indices = index.search(embedding, k)
    if with_distance:
        return [(target_list[index], distances[0][i]) for i, index in enumerate(indices[0])]
    return [target_list[i] for i in indices[0]]

# Cell

#!/usr/bin/env python
import functools

# import visualise_spacy_pattern
import json
from collections import defaultdict
from io import BytesIO
from operator import itemgetter
from typing import Dict, List, Union

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import spacy
from spacy import displacy
from spacy.lemmatizer import ADJ, NOUN, VERB, Lemmatizer
from spacy.matcher import DependencyMatcher
from spacy.pipeline import merge_entities
from spacy.tokens import Doc, Span, Token
from typeguard import typechecked
import en_core_web_sm

# import en_core_sci_md, en_core_sci_sm

# tip: Use Code Folding


def ents_w_candidates(doc):
    return [(ent, candidates_lables(ent)) for ent in doc.ents]


@typechecked
def candidates_lables(ent: Span) -> List:
    """aggregates labels from possibly multiple NER models (bc5, bionlpa...)"""
    return [cand["label"] for cand in ent._.annotated]


@typechecked
def get_ent_from_token(token: Token, doc: Doc) -> List[Span]:
    """Entities can have multiple tokens"""
    return [ent for ent in doc.ents if ent.start_char <= token.idx <= ent.end_char]


def load_sci_pipe(model="en_core_sci_md"):
    nlp = spacy.load(model)
    abbreviation_pipe = AbbreviationDetector(nlp)

    nlp.add_pipe(abbreviation_pipe)
    nlp.add_pipe(merge_entities)
    return nlp


# this might make trouble since it's a list of spans without the .DOC API methods?
def m_reannotate():
    """Takes deserialized doc.user_data with the doc's custom_attributes data and
    sets the ._.annotated attribute again on the entity so it's easier to process later"""
    # strangely two entries with different spans for some entities in
    # user_data as in ._.annotated although user_data is generated by ._.annotated
    try:
        Span.set_extension("annotated", default=[], force=True)
    except:
        5
    # except:
    #     for k,v in doc.user_data.items():
    #         for ent in doc.ents:
    #             #print(k, v, k[2])
    #             if ent.start_char == k[2]:
    #                 #print(type(v), v)
    #                 #converting to list to be consistent with merge_docs and other notebooks ._.annotated
    #                 ent._.annotated = list(v)# if type(v) == tuple else []


def last_token_of_entity(doc: Doc, token: Token) -> Token:
    """RECURSIVE. Given a token in an entity, it recurses to the right until it finds a token where the IOB is not Inside (I)"""
    """ HMGB1-induced -> induced"""
    next_token = token.nbor()
    is_end = next_token.ent_iob != 1
    if is_end:
        return token
    else:
        return last_token_of_entity(doc, next_token)


def negated_ents(doc: Doc) -> List[Span]:
    """Returns List of all Entities that have a True flag under ._.negex"""
    return [ent for ent in doc.ents if ent._.negex]


def show_negex_entities(docs: List[Doc]) -> List[Dict]:
    """Shows the negated entities of that sentence (estimated by patterns inside negSpacy). Filters out sentences with no negations"""
    ent_pat = {}
    for doc in docs:
        ent_pat[doc.text] = negated_ents(doc)
    return [{k: ent_pat[k]} for k in ent_pat if len(ent_pat[k])]


def get_token_and_entities_as_spans(doc: Doc) -> List[Span]:
    """
    Possibly merge_entities does this but...
    Helpful if you need a list of token and entities together. Tokens that are part of an entity are merged
    Takes a Doc and gives you an iterable that doc.ents or doc[..] can't. It groups token by entity and maintains orginal doc order"""
    spans = []
    idx = 0
    while idx < len(doc):
        print(idx, type(idx))
        token = doc[idx]
        if token.ent_iob == 3:  # beginning of entity
            end_token = last_token_of_entity(doc, token)
            print(token, end_token)
            spans.append(doc[token.i : end_token.i + 1])
            idx = end_token.i + 1  # don't have an endless while loop
        else:
            idx = idx + 1
            spans.append(doc[token.i])
    return spans


def add_pipes_mutative(nlps, linker):
    """add pipeline components to every nlp pipeline """
    for nlp in nlps:  # mutative
        abbreviation_pipe = AbbreviationDetector(nlp)
        nlp.add_pipe(abbreviation_pipe)
        nlp.add_pipe(merge_entities)
        nlp.add_pipe(linker)
    return nlps


# @typechecked
# def get_ont_name(
#     linker: EntityLinker,
# ) -> str:  # assumes a lot on consistent naming in scispacy
#     "GeneOntology or UMLS or MESH"
#     return str(linker.kb).split(".")[2].split(" ")[0]


def rsetattr(obj, attr, val):
    """setting nested attributes"""
    pre, _, post = attr.rpartition(".")
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, path: str, *default):
    """
    :param obj: Object
    :param path: 'attr1.attr2.etc'
    :param default: Optional default value, at any point in the path
    :return: obj.attr1.attr2.etc
    """
    DELIMITER = "."
    attrs = path.split(DELIMITER)
    try:
        return functools.reduce(getattr, attrs, obj)
    except AttributeError:
        if default:
            return default[0]
        raise


@typechecked
def get_entity_diff(
    doc: Doc, new_ents_info: List[dict]
):  # candidates= [{start, end, label_, label}]
    """Looks if there is an  entity match at the exact same position of another document (with another pipeline)
    . If yes, the new overrides the old. How to merge docs, if it is at all a good idea is a mystery to me
    """
    seen_tokens = set()
    new_entities = []
    old_entities = doc.ents
    for named_ent in new_ents_info:  # every entity
        start_char, end_char, label = itemgetter("start_char", "end_char", "label_")(
            named_ent
        )
        start = get_tokenidx_for_char(doc, start_char)
        end = get_tokenidx_for_char(doc, end_char)
        #    span = Span(doc, start, end, label=match_id)
        #    doc.ents = list(doc.ents) + [span]
        # check for end - 1 here because boundaries are inclusive
        try:
            if start not in seen_tokens and end - 1 not in seen_tokens:
                entity = Span(doc, start, end, label=label)
                new_entities.append(entity)

                # compare by token idx
                old_entities = [
                    e for e in old_entities if not (e.start < end and e.end > start)
                ]

                # compare by char_offset (should have same results)
                # old_entities = [ e for e in old_entities if not (e.start_char < end_char and e.end_char > start_char)]

                seen_tokens.update(range(start, end))
        except TypeError:
            "mehhh token index is off -- have to do this func on the char_level"
    return old_entities, new_entities


@typechecked
def merge_named_entities(
    docA: Doc, docB: Doc, merge_from_model: str, model_kb_name: str
):
    """Merges two docs and places the kb_ents as extension with the ontology and model name.
    So if two entities merge, the old entities can still be found on the object (EXCEPT! Base_doc ...because it is not NER just ER)
    """
    ents_info = extract_named_entities_info(docB)
    old_entities, new_entities = get_entity_diff(docA, ents_info)
    # print(type(new_entities[0]), new_entities[0]._.kb_ents)
    if len(new_entities):
        # if(getattr(new_entities[0], "_." + "model_labels")
        new_entities[0].set_extension("annotated", default=[], force=True)
        # new_entities[0].set_extension(merge_from_model, default={}, force=True)

        for idx, named_ent in enumerate(new_entities):
            kb_ents = ents_info[idx]["kb_ents"]
            # print("kb_ents", kb_ents)

            infos = rgetattr(named_ent, "_." + "annotated")

            # EVERY entity gets an info object
            info = {
                "idx": idx,
                "kb_ents": kb_ents,
                "label": named_ent.label_,
                "model": model_kb_name,
                "end_char": named_ent.end_char,
                "start_char": named_ent.start_char,
            }
            infos.append(info)
            """


            info
            info[]
            info["label"] = named_ent.label_
            info["end_char"] = named_ent.end_char
            info["start_char"] = named_ent.start_char
            """

            rsetattr(named_ent, "_." + "annotated", infos)
            # rsetattr(named_ent, "_." + "labels." + merge_from_model, named_ent.label_)
            # rsetattr(named_ent, "_." + "labels"), {model_kb_name: kb_ents})

    # TODO: sets --> check who overwrites whom (only if entities named) --> especially after first model
    # aka filter(has_label, old_entities).intersect(new_entities)
    return tuple(old_entities) + tuple(new_entities)  # merged_doc


def print_table(rows, padding=0):
    """ Print `rows` with content-based column widths. """
    col_widths = [max(len(str(value)) for value in col) + padding for col in zip(*rows)]
    total_width = sum(col_widths) + len(col_widths) - 1
    fmt = " ".join("%%-%ds" % width for width in col_widths)
    print(fmt % tuple(rows[0]))
    print("~" * total_width)
    for row in rows[1:]:
        print(fmt % tuple(row))


def show_noun_chunks(doc: Doc):
    rows = [["Chunk", ".root", "root.dep_", ".root.head"]]
    for chunk in doc.noun_chunks:
        rows.append(
            [
                chunk,  # A Span object with the full phrase.
                chunk.root,  # The key Token within this phrase.
                chunk.root.dep_,  # The grammatical role of this phrase.
                chunk.root.head,  # The grammatical parent Token.
            ]
        )
    print_table(rows, padding=4)


@typechecked
def doc_has_entity_labels(doc, ent_labels: List[List[str]]):
    """Checks if a pair of entities (two lists of aliases) show up in a document. For sentence level checks: .... maybe something else"""
    for idx, ent in enumerate(doc.ents):
        doc_labels = [
            annotation["label"] for ent in doc.ents for annotation in ent._.annotated
        ]
        return any([label in doc_labels for label in ent_labels[0]]) and any(
            [label in doc_labels for label in ent_labels[1]]
        )
    return False


@typechecked
def get_merged_docs_for_texts(
    texts: List[str], base_nlp, NER_nlps: List, print_every_nth: 25
) -> List[Doc]:
    print(
        "Merging Named Entities (Chems, Gene, Organism etc.). Later docs in the pipeline overwrite entities from earlier ones"
    )
    docs = []
    span_overflow_errors = []
    for idx, text in enumerate(texts):
        doc = base_nlp(text)
        for nlp in NER_nlps:  # later nlps overwrite entities of earlier ones
            try:
                next_doc = nlp(text)
                doc.ents = merge_named_entities(doc, next_doc, nlp.meta["name"], "umls")
            except IndexError:
                span_overflow_errors.append(
                    "index : " + str(idx) + " --- error for doc: " + text[:10]
                )
        docs.append(doc)
        if len(docs) % print_every_nth == 0:
            print("processed " + len(docs))
    [print(errormsg) for errormsg in span_overflow_errors]

    return docs


def get_tokenidx_for_char(doc, char_idx):
    """
    adapted from https://stackoverflow.com/questions/55109468/spacy-get-token-from-character-index
    """
    for index, token in enumerate(doc):
        if char_idx > token.idx:
            continue
        if char_idx == token.idx:
            return token.i
        if char_idx < token.idx:
            return doc[index].i  # here maybe index-1 ...


def extract_named_entities_info(doc) -> List[dict]:
    """Get important props from the spacy entity object"""
    # keys=["start", "end", "label_"] #span can't be accessed with bracket notation....
    ents_info = []
    # this is stupid, but Span doesn't do dictionary comprehension API
    for ent in doc.ents:
        info = {}
        info["start"] = ent.start
        info["end"] = ent.end
        info["start_char"] = ent.start_char
        info["end_char"] = ent.end_char
        info["label_"] = ent.label_
        info["kb_ents"] = ent._.kb_ents
        ents_info += [info]
    return ents_info


def pattern_vis(pattern: List[dict]):
    print("png display not working.. something stupid about pydot")
    """ graph = visualise_spacy_pattern.to_pydot(pattern)
    # render pydot by calling dot, no file saved to disk
    png = graph.create_png(prog="dot")
    #graph_file = 'graph1.png'.format()

    # treat the dot output string as an image file
    sio = BytesIO()
    sio.write(png)
    sio.seek(0)
    img = mpimg.imread(sio)

    fig = plt.figure()
    fig.set_size_inches(6,6)

    img=mpimg.imread(png)
    imgplot = plt.imshow(img,vmin=600)
    plt.show()"""


def prep_pattern(pattern: str) -> List[List[str]]:
    return [rule.split("|") for rule in pattern.split(" ")]


def add_matches(
    vocab,
    patterns: List[str],
    lemmas=True,
    start_ents=None,
    end_ents=None,
    print_patterns=False,
):
    # BAAAAD PATTERN! PASSING DOWN VARS (DECORATOR?)
    """Converts "prevented|nsubj|START_ENTITY prevented|dobj|END_ENTITY"
    into a pattern that DependencyMatcher class can use"""
    matcher = DependencyMatcher(vocab)
    for p in patterns:
        pattern = construct_pattern(
            p, lemmatize=lemmas, start_ents=start_ents, end_ents=end_ents
        )
        if print_patterns:
            print(pattern, p)
        try:  # object of type 'NoneType' has no len() weirdly on some of the 20k dep paths
            matcher.add(p, None, pattern)
        except:
            print("error with pattern", p, "-->", pattern)
            continue
    return matcher


def get_lemma(verb, V=True, model=None):  # nlp
    if model:
        nlp = model
    else:
        nlp = en_core_web_sm.load()


    lemmatizer = nlp.vocab.morphology.lemmatizer  # lemmatizer("is") -> "be"
    return lemmatizer(verb, VERB)[0]


def check_for_non_trees(rules: List[List[str]]):

    parent_to_children = defaultdict(list)
    seen = set()
    has_incoming_edges = set()
    for (parent, rel, child) in rules:
        seen.add(parent)
        seen.add(child)
        has_incoming_edges.add(child)
        if parent == child:
            return None
        parent_to_children[parent].append((rel, child))

    # Only accept strictly connected trees.
    roots = seen.difference(has_incoming_edges)
    if len(roots) != 1:
        return None

    root = roots.pop()
    seen = {root}

    # Step 2: check that the tree doesn't have a loop:
    def contains_loop(node):
        has_loop = False
        for (_, child) in parent_to_children[node]:
            if child in seen:
                return True
            else:
                seen.add(child)
                has_loop = contains_loop(child)
            if has_loop:
                break

        return has_loop

    if contains_loop(root):
        return None

    return root, parent_to_children


def annotate_NER(model, gpu=False):
    """"""
    model(gpu)

def construct_pattern_old(rules: List[List[str]]):
    """
    Idea: add patterns to a matcher designed to find a subtree in a spacy dependency tree.
    Rules are strictly of the form "CHILD --rel--> PARENT". To build this up, we add rules
    in DFS order, so that the parent nodes have already been added to the dict for each child
    we encounter.
    """
    # Step 1: Build up a dictionary mapping parents to their children
    # in the dependency subtree. Whilst we do this, we check that there is
    # a single node which has only outgoing edges.

    if "dep" in {rule[1] for rule in rules}:
        return None

    ret = check_for_non_trees(rules)

    if ret is None:
        return None
    else:
        root, parent_to_children = ret

    def add_node(parent: str, pattern: List):

        for (rel, child) in parent_to_children[parent]:

            # First, we add the specification that we are looking for
            # an edge which connects the child to the parent.
            node = {
                "SPEC": {
                    "NODE_NAME": child,
                    "NBOR_RELOP": ">",
                    "NBOR_NAME": parent},
            }

            # DANGER we can only have these options IF we also match ORTH below, otherwise it's torturously slow.
            # token_pattern = {"DEP": {"IN": ["amod", "compound"]}}

            # Now, we specify what attributes we want this _token_
            # to have - in this case, we want to match a certain dependency
            # relation specifically.
            token_pattern = {"DEP": rel}

            # Additionally, we can specify more token attributes. So here,
            # if the node refers to the start or end entity, we require that
            # the word is part of an entity (spacy syntax is funny for this)
            # and that the word is a noun, as there are some verbs annotated as "entities" in medmentions.

            if child in {"START_ENTITY", "END_ENTITY"}:
                token_pattern["ENT_TYPE"] = {"NOT_IN": [""]}
                token_pattern["POS"] = "NOUN"

            # If we are on part of the path which is not the start/end entity,
            # we want the word to match. This could be made very flexible, e.g matching
            # verbs instead, etc.
            else:
                token_pattern["ORTH"] = child

            node["PATTERN"] = token_pattern

            pattern.append(node)
            add_node(child, pattern)

    pattern = [{"SPEC": {"NODE_NAME": root}, "PATTERN": {"ORTH": root}}]
    add_node(root, pattern)

    assert len(pattern) < 20
    return pattern

def construct_pattern(
    rules: List[List[str]], lemmatize=True, start_ents=None, end_ents=None, log_info=[]
):
    """
    Idea: add patterns to a matcher designed to find a subtree in a spacy dependency tree.
    Rules are strictly of the form "CHILD --rel--> PARENT". To build this up, we add rules
    in DFS order, so that the parent nodes have already been added to the dict for each child
    we encounter.
    """
    # Step 1: Build up a dictionary mapping parents to their children
    # in the dependency subtree. Whilst we do this, we check that there is
    # a single node which has only outgoing edges.

    if type(rules) is str:
        rules = prep_pattern(rules)

    if "dep" in {rule[1] for rule in rules}:
        return None

    ret = check_for_non_trees(rules)

    if ret is None:
        return None
    else:
        root, parent_to_children = ret

    def add_node(parent: str, pattern: List):

        for (rel, child) in parent_to_children[parent]:

            # First, we add the specification that we are looking for
            # an edge which connects the child to the parent.
            node = {
                "SPEC": {"NODE_NAME": child, "NBOR_RELOP": ">", "NBOR_NAME": parent},
            }

            # DANGER we can only have these options IF we also match ORTH below, otherwise it's torturously slow.
            # token_pattern = {"DEP": {"IN": ["amod", "compound"]}}

            # Now, we specify what attributes we want this _token_
            # to have - in this case, we want to match a certain dependency
            # relation specifically.
            token_pattern = {"DEP": rel}

            # Additionally, we can specify more token attributes. So here,
            # if the node refers to the start or end entity, we require that
            # the word is part of an entity (spacy syntax is funny for this)
            # and that the word is a noun, as there are some verbs annotated as "entities" in medmentions.

            # TODO: variable entities pair matchings
            # if child in {"start_entity", "end_entity", "START_ENTITY", "END_ENTITY"}:
            #   #print(child, "ahe")
            #   token_pattern["ENT_TYPE"] = {"IN": ["SIMPLE_CHEMICAL", "GENE_OR_GENE_PRODUCT"]}
            #   token_pattern["POS"] = "NOUN"

            if str.lower(child) in {"start_entity", "end_entity"}:
                #!UNCOMMENT BELOW IFF ONLY TOKENS that also have ENTITIES can be in the match-subtree!!
                token_pattern["ENT_TYPE"] = {"NOT_IN": [""]}

                if start_ents and end_ents:
                    6
                    # TODO! THIS DOESN"T WORK YET, bc ENT_TYPE looks on label, not ._. our custom attrs
                    # token_pattern["ENT_TYPE"] = {"NOT_IN": start_ents + end_ents}

                token_pattern["POS"] = "NOUN"

            # If we are on part of the path which is not the start/end entity,
            # we want the word to match. This could be made very flexible, e.g matching
            # verbs instead, etc.
            else:
                token_pattern["ORTH"] = child

            node["PATTERN"] = token_pattern

            pattern.append(node)
            add_node(child, pattern)

    root_pattern = {"ORTH": root}
    if lemmatize:
        root_pattern = {"LEMMA": get_lemma(root)}
    pattern = [{"SPEC": {"NODE_NAME": root}, "PATTERN": root_pattern}]
    add_node(root, pattern)

    assert len(pattern) < 20
    return pattern


# pattern = [
#     {"SPEC": {"NODE_NAME": "prevented"}, "PATTERN": {"ORTH": "prevented"}},
#     {"SPEC": {"NODE_NAME": "start_entity", "NBOR_RELOP": ">", "NBOR_NAME": "prevented"}, "PATTERN": {"DEP": "nsubj"}},
#     {"SPEC": {"NODE_NAME": "release", "NBOR_RELOP": ">", "NBOR_NAME": "prevented"}, "PATTERN": {"DEP": "dobj", "ORTH":"release"}},
#     {"SPEC": {"NODE_NAME": "end_entity", "NBOR_RELOP": ">", "NBOR_NAME": "release"}, "PATTERN": {"DEP": "nmod"}},

# ]


# @typechecked
def match_texts(matcher: DependencyMatcher, docs: List[Union[Doc, str]], nlp) -> dict:
    output = {}
    if type(docs[0]) == str:
        docs = [nlp(text) for text in docs]
    for doc in docs:
        matches = matcher(doc)
        # print(matches, 'match')
        for match_id, ms in matches:
            rule_id = nlp.vocab.strings[
                match_id
            ]  # get name of the pattern, i.e. 'x|prevented|y'

            if len(ms):
                start = min(ms[0])
                end = max(ms[0])

                sents = [doc[start].sent]
                # in case there a relation spans two sentences ... usually not
                if doc[start].sent != doc[end].sent:
                    sents = [doc[start].sent, doc[end].sent]

                span = doc[start : end + 1]

                doc_match = {
                    "doc_idx": len(docs) - 1,
                    "span": span.text or "---",
                    "sents": sents,
                    "matches": ms,
                    "sent_ents": [sent.ents for sent in sents],
                }
                if rule_id not in output:
                    output[rule_id] = []
                # print("HIT", doc_match)
                output[rule_id].append(doc_match)
    return output


# show_tabs(doc)
