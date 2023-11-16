from gensim.models import Word2Vec, KeyedVectors
import ast
import numpy as np
from sklearn.cluster import KMeans
import re
import gensim.downloader as api
from gensim.scripts.glove2word2vec import glove2word2vec

from utils import load_data

def words_to_sentence(word_list):
    return " ".join(word_list)

def remove_words_with_numbers(word_list_str):
    """
    Takes a string representation of a list of words as input,
    removes any special characters from the words, and then removes any words that contain numbers.

    Args:
      word_list_str: A string representation of a list of words.

    Returns:
      The function `remove_words_with_numbers` returns a list of words without any special characters or
    numbers.
    """
    word_list = ast.literal_eval(word_list_str)
    word_list_without_special = [
        re.sub(r"[^a-zA-Z0-9\s]", "", word) for word in word_list
    ]
    word_list_without_numbers = [
        word for word in word_list_without_special if not re.search(r"\d", word)
    ]
    return word_list_without_numbers

df = load_data(kind="processed")

# Apply the function to the 'words' column of the DataFrame
# df["description"] = df["description"].apply(
#     lambda x: remove_words_with_numbers(x)
# )

##### GLOVE #######


def load_glove_model(glove_file_path, expected_size=100):
    """
    Load the GloVe model from the specified file path.
    Only includes vectors that match the expected dimensionality.
    """
    glove_model = {}
    with open(glove_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            split_line = line.split()
            if len(split_line) != expected_size + 1:  # +1 for the word itself
                continue  # Skip lines that don't have the expected number of dimensions
            word = split_line[0]
            embedding = np.array([float(val) for val in split_line[1:]])
            glove_model[word] = embedding
    return glove_model

# Path to the GloVe file
glove_file = "models/glove.twitter.27B/glove.twitter.27B.100d.txt" # Update the path to your GloVe file

glove_model = load_glove_model(glove_file)

# Convert GloVe model to KeyedVectors format for compatibility with Gensim functions
word_vectors = KeyedVectors(vector_size=glove_model[next(iter(glove_model))].shape[0])

# Add vectors to KeyedVectors
for word, vector in glove_model.items():
    try:
        word_vectors.add_vector(word, vector)
    except Exception as e:
        print(f"Error adding vector for {word}: {e}")

# Function to convert description to vector
def description_to_vector(description, model):
    words = description.split()  # Adjust if your descriptions are formatted differently
    valid_vectors = [model[word] for word in words if word in model]
    
    if valid_vectors:
        return np.mean(valid_vectors, axis=0)
    else:
        return np.zeros(model.vector_size)

# Apply the function to each description
df['vector'] = df['description'].apply(lambda desc: description_to_vector(desc, word_vectors))



##########################################

##### PRETRAINED MODEL WORD2VEC ######
# model = KeyedVectors.load_word2vec_format('models/GoogleNews-vectors-negative300.bin', binary=True)
# def description_to_vector(description, model):
#     valid_words = [word for word in description if word in model.key_to_index]
#     if valid_words:
#         return np.mean([model[word] for word in valid_words], axis=0)
#     else:
#         return np.zeros(model.vector_size)
# df['vector'] = df['description'].apply(lambda desc: description_to_vector(desc, model))
###################################

######### Word2Vec #########
# model = Word2Vec(sentences=df['description'], vector_size=100, window=5, min_count=1, workers=4)
# def description_to_vector(description):
#     # Filter out words not in the model's vocabulary
#     valid_words = [word for word in description if word in model.wv.key_to_index]
#     if valid_words:
#         # Average the vectors of the words in the description
#         return np.mean(model.wv[valid_words], axis=0)
#     else:
#         # If no valid words, return a zero vector
#         return np.zeros(model.vector_size)

# df['vector'] = df['description'].apply(description_to_vector)
##################################
# Convert list of vectors to a 2D array for clustering
vectors = np.array(df['vector'].tolist())

# Apply KMeans clustering
kmeans = KMeans(n_clusters=20) 
df['cluster'] = kmeans.fit_predict(vectors)

df_id_and_cluster = df[["id", "cluster"]].sort_values(
    by="cluster", ascending=True
)
df_id_and_cluster.to_csv("./csv_files/word2wev_clustering_id.csv", index=False)