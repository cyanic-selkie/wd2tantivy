import tantivy
import argparse
import unicodedata
import spacy
from itertools import groupby, islice, repeat
from multiprocessing import Pool, cpu_count
from typing import List, Tuple
import sys

nlp = None
def worker_init(model: str):
    global nlp
    nlp = spacy.load(model, disable=["senter", "parser", "ner"])

def worker(input: Tuple[str, str]):
    global nlp

    line, language = input

    line = line.strip()
    
    # QID
    pattern = "<http://www.wikidata.org/entity/Q"
    if not line.startswith(pattern):
        return None

    i = line[len(pattern):].find(">")

    qid = int(line[len(pattern):len(pattern) + i])

    line = line[len(pattern) + i + 2:]

    # PROPERTY
    patterns = [
        "<http://www.w3.org/2004/02/skos/core#altLabel>",
        "<http://www.w3.org/2004/02/skos/core#prefLabel>",
        "<http://www.w3.org/2000/01/rdf-schema#label>",
        "<http://schema.org/name>",
    ]
    pattern = None
    priority = None
    for i, x in enumerate(patterns):
        if line.startswith(x):
            pattern = x
            priority = i
            break

    if not pattern:
        return None

    line = line[len(pattern) + 1:]

    # ALIAS
    if not line.endswith(f"@{language} ."):
        return None

    line = line[:-(len(language) + 3)]
    alias = line.encode('ascii').decode('unicode-escape')[1:-1]
    alias = unicodedata.normalize("NFC", alias)

    if alias == "":
        return None

    lemmatized_alias = " ".join(token.lemma_.lower() for token in nlp(alias) if not token.is_stop and not token.is_punct)

    return qid, alias, lemmatized_alias, priority

def main():    
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--language", type=str, required=True)
    parser.add_argument("--spacy-model", type=str, required=True)
    args = parser.parse_args()

    schema_builder = tantivy.SchemaBuilder()
    schema_builder.add_integer_field("qid", stored=True, indexed=True)
    schema_builder.add_text_field("name", stored=True, index_option='basic')
    schema_builder.add_text_field("alias", stored=True)
    schema = schema_builder.build()

    index = tantivy.Index(schema, path=args.output)
    writer = index.writer()

    with Pool(processes=cpu_count(), initializer=worker_init, initargs=(args.spacy_model,)) as pool:
        for qid, output in groupby(filter(None, pool.imap(worker, zip(sys.stdin, repeat(args.language)), chunksize=1000)), lambda x: x[0]):
            output = list(output)

            name = None
            priority = None
            aliases = set()

            for _, _alias, _lemmatized_alias, _priority in output:
                if not name or _priority > priority:
                    name = _alias
                    priority = _priority

                aliases.add(_lemmatized_alias)

            if len(aliases) == 0:
                continue

            writer.add_document(tantivy.Document(
                qid=qid,
                name=name,
                alias=list(aliases),
            ))

        writer.commit()

if __name__ == "__main__":
    main()
