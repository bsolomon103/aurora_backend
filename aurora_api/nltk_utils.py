import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import numpy as np

def tokenize(sentence):
    return word_tokenize(sentence)

def stemming(word):
    return PorterStemmer().stem(word.lower())

def bag_of_words(tokenized_sentence, all_words):
    tokenized_sentence = [stemming(w) for w in tokenized_sentence]
    bag = np.zeros(len(all_words), dtype=np.float32)
    for index, words in enumerate(all_words):
        if words in tokenized_sentence:
            bag[index] = 1.0
    return bag
    