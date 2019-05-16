
"""restrictions for input files:
    -a sentence should not be splitted into multiple lines
"""

from os import listdir
from os.path import isdir, isfile, join
from nltk.tokenize import sent_tokenize, WordPunctTokenizer
from typing import List, Iterable
from gensim.models import FastText
from gensim.models.wrappers import FastText as FastTextWrapper
import sys
import csv
sys.path.insert(0, '/home/teo/repos/Readerbench-python/')

from rb.parser.spacy_parser import SpacyParser
from rb.core.lang import Lang
from rb.core.document import Document

import random
import string
from typodistance import typoGenerator
from mistake import Mistake 


class CorpusGenerator():


    PATH_RAW_CORPUS = "books/"
    MIN_SENT_TOKENS = 6
    CORRECT_DIACS = {
        "ş": "ș",
        "Ş": "Ș",
        "ţ": "ț",
        "Ţ": "Ț",
    }
    MAX_SENT_TOKENS = 18
    #FAST_TEXT = "/home/teo/projects/readme-models/models/fasttext_fb/wiki.ro"
    FAST_TEXT = "/home/teo/repos/langcorrections/fasttext_fb/wiki.ro"

    def __init__(self):
        self.files = []
        for f in listdir(CorpusGenerator.PATH_RAW_CORPUS):
            if isfile(join(CorpusGenerator.PATH_RAW_CORPUS, f)) and f.endswith(".txt"):
                self.files.append(join(CorpusGenerator.PATH_RAW_CORPUS, f))
        
        self.parser = SpacyParser.get_instance().get_model(Lang.RO)
        #self.fasttext = FastText.load(CorpusGenerator.FAST_TEXT)
        #self.fasttext = FastTextWrapper.load_fasttext_format(CorpusGenerator.FAST_TEXT)
                
    def split_sentences(self, fileName: str) -> Iterable[List[str]]:
        # sentences = []
        tokenizer = WordPunctTokenizer()
        with open(fileName, "rt", encoding='utf-8') as f:
            for line in f.readlines():
                for sent in sent_tokenize(line):
                    yield sent

    def modify_word(self, token, mistake_type):
        text_token = token.text
        try:
            if mistake_type is Mistake.TYPO:
                typo = random.choice([x for x in typoGenerator(text_token, 2)][1:])
                return typo
            elif mistake_type is Mistake.INFLECTED:
                # candidates = self.fasttext.similar_by_word(token.lemma_, topn=200)
                if token.text not in self.word_to_lemma[token.text]:
                    lemma = token.lemma_
                else:
                    lemma = self.word_to_lemma[token.text]

                if lemma in self.lemma_to_words:
                    candidates = self.lemma_to_words[lemma]
                    potential = random.choice(candidates)
                    if potential != token.text:
                        return potential
                else:
                    print(lemma, token.text, 'y')
            return None
        except:
            return None
    
    def clean_text(self, text: str):
        list_text = list(text)
        # some cleaning correct diacritics + eliminate \
        text = "".join([CorpusGenerator.CORRECT_DIACS[c] if c in CorpusGenerator.CORRECT_DIACS else c for c in list_text])
        return text.lower()

    def construct_lemma_dict(self, lemma_file="wordlists/lemmas_ro.txt"):
        self.word_to_lemma = {}
        self.lemma_to_words = {}

        with open(lemma_file, 'r') as f:
            for line in f:
                line = line.split()
                line[0] = line[0].strip()
                line[1] = line[1].strip()
                if len(line) != 2:
                    continue
                self.word_to_lemma[line[0]] = line[1]
                if line[1] not in self.lemma_to_words:
                    self.lemma_to_words[line[1]] = [line[0]]
                else:
                    self.lemma_to_words[line[1]].append(line[0])
        print('lemmas: {}'.format(len(self.lemma_to_words)))
        print('words: {}'.format(len(self.word_to_lemma)))

    def generate(self):
        self.construct_lemma_dict() 
        lines = []
        for ffile in self.files:
            for i, sent in enumerate(self.split_sentences(ffile)):
                line = []
                if len(lines) % 100 == 0:
                    print(len(lines))

                if len(lines) > 1e6:
                    break

                sent = self.clean_text(sent)
                docs_ro = self.parser(sent)
                tokens = [token for token in docs_ro]
                text_tokens = [token.text for token in docs_ro]
                sent2 = " ".join(text_tokens)
                try:
                    if len(tokens) >= CorpusGenerator.MIN_SENT_TOKENS and len(tokens) <= CorpusGenerator.MAX_SENT_TOKENS:
                        count_tries = 0
                        while count_tries < 20:
                            index = random.randint(0, len(tokens) - 1)
                            tagg = str(tokens[index].tag_)
                            if (tagg.startswith("P") or tagg.startswith("COMMA")
                                or tagg.startswith("DASH") or tagg.startswith("COLON")
                                or tagg.startswith("QUEST") or tagg.startswith("HELLIP")
                                or tagg.startswith("DBLQ") or tagg.startswith("EXCL")): # punctuation
                                count_tries += 1
                                continue
                            text_tok = self.modify_word(tokens[index], Mistake.INFLECTED)
                            if text_tok is not None:
                                text_tokens[index] = text_tok
                                sent3 = " ".join(text_tokens)
                                line.append(sent2)
                                line.append(sent3)
                                line.append(tokens[index].tag_)
                                line.append(Mistake.INFLECTED.value)
                                break
                            else:
                                count_tries += 1
                                continue
                            count_tries += 1
                except:
                    line = []
                  
                if len(line) > 1:
                    lines.append(line)
        print(len(lines))
        with open('inflected_2.csv', 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerows(lines)  
        # print(self.files)
        # for x in self.split_sentences(self.files[0]):
        #     print(x)

if __name__ == "__main__":
    corpusGenerator = CorpusGenerator()
    corpusGenerator.generate()
    #corpusGenerator.generate()
