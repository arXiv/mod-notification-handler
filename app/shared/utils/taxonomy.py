"""taxonomy helpers shared by all jobs"""
from arxiv.taxonomy.definitions import CATEGORY_ALIASES

#reverse of CATEGORY_ALIASES: canonical id -> alias id (e.g. econ.GN -> q-fin.EC)
ALIAS_BY_CANONICAL = {v: k for k, v in CATEGORY_ALIASES.items()}
